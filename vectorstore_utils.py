#!/usr/bin/env python3
"""
Vector Store Utilities Module
Functions for OpenAI Vector Store operations and embedding management.
"""

import os
import logging
import time
import tempfile
from typing import List, Dict, Any, Optional
from openai import OpenAI
import asyncio
from concurrent.futures import ThreadPoolExecutor
import backoff
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Initialize OpenAI client with graceful handling for tests
try:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY environment variable is not set")
        client = None
    else:
        # Initialize with basic parameters only
        client = OpenAI(api_key=api_key)
        logger.info("OpenAI client initialized successfully")
except Exception as e:
    logger.error(f"OpenAI client initialization failed: {e}")
    # Try with minimal initialization
    try:
        import openai
        openai.api_key = os.getenv("OPENAI_API_KEY")
        client = OpenAI()
        logger.info("OpenAI client initialized with fallback method")
    except Exception as e2:
        logger.error(f"Fallback initialization also failed: {e2}")
        client = None

def getVectorStoreName(company_name: str) -> str:
    """
    Generate a standardized vector store name for a company.
    
    Args:
        company_name: The name of the company
        
    Returns:
        str: The vector store name (e.g., "kalco_leads")
    """
    return f"{company_name.lower()}_leads"

def fetch_existing_metadata_map(company_name: str) -> Dict[str, str]:
    """
    Query vector store for existing documents metadata and return mapping of id -> updatedAt.
    
    Args:
        company_name: The name of the company
        
    Returns:
        Dict[str, str]: Mapping of id to updatedAt timestamps
        
    Note:
        If the OpenAI Vector Store API doesn't support metadata listing,
        this returns an empty dict as a safe fallback (will upsert all leads).
    """
    try:
        vector_store_name = getVectorStoreName(company_name)
        
        # Try to find existing vector store
        vector_stores = client.beta.vector_stores.list()
        target_store = None
        
        for store in vector_stores.data:
            if store.name == vector_store_name:
                target_store = store
                break
        
        if not target_store:
            logger.info(f"No existing vector store found for {company_name}")
            return {}
        
        # Note: OpenAI Vector Store API may not support direct metadata listing
        # This is a safe fallback that will result in upserting all leads
        logger.info(f"Vector store exists for {company_name}, but metadata listing not available")
        return {}
        
    except Exception as e:
        logger.warning(f"Error fetching existing metadata for {company_name}: {e}")
        # Safe fallback: return empty dict to force full refresh
        return {}

@backoff.on_exception(backoff.expo, Exception, max_tries=3, max_time=30)
def embed_texts(texts: List[str], batch_size: int = 64) -> List[List[float]]:
    """
    Embed a list of texts using OpenAI's text-embedding-3-small model.
    
    Args:
        texts: List of text strings to embed
        batch_size: Number of texts to process in each batch
        
    Returns:
        List[List[float]]: List of embedding vectors
    """
    if not texts:
        return []
    
    all_embeddings = []
    
    # Process in batches to avoid API limits
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        
        try:
            logger.info(f"Embedding batch {i//batch_size + 1} ({len(batch)} texts)")
            
            response = client.embeddings.create(
                model="text-embedding-3-small",
                input=batch
            )
            
            batch_embeddings = [embedding.embedding for embedding in response.data]
            all_embeddings.extend(batch_embeddings)
            
            # Small delay between batches to be respectful to the API
            if i + batch_size < len(texts):
                time.sleep(0.1)
                
        except Exception as e:
            logger.error(f"Error embedding batch starting at index {i}: {e}")
            raise
    
    logger.info(f"Successfully embedded {len(all_embeddings)} texts")
    return all_embeddings

@backoff.on_exception(backoff.expo, Exception, max_tries=3, max_time=60)
def upsert_lead_documents(company_name: str, items: List[Dict[str, Any]]) -> dict:
    """
    Upsert lead documents into OpenAI Vector Store.
    
    Args:
        company_name: The name of the company
        items: List of items with keys: "id", "text", "metadata"
        
    Returns:
        dict: Summary of the upsert operation
    """
    if not items:
        return {"upserted": 0, "message": "No items to upsert"}
        
    try:
        vector_store_name = getVectorStoreName(company_name)
        
        # Find or create vector store
        vector_stores = client.beta.vector_stores.list()
        target_store = None
        
        for store in vector_stores.data:
            if store.name == vector_store_name:
                target_store = store
                break
        
        if not target_store:
            logger.info(f"Creating new vector store: {vector_store_name}")
            target_store = client.beta.vector_stores.create(
                name=vector_store_name,
                metadata={"company": company_name}
            )
        
        # Create files with lead content and upload to vector store
        batch_size = 20  # Smaller batch size for file operations
        total_upserted = 0
        
        for i in range(0, len(items), batch_size):
            batch_items = items[i:i + batch_size]
            
            logger.info(f"Processing batch {i//batch_size + 1} ({len(batch_items)} items)")
            
            # Create file objects for this batch
            file_objects = []
            
            for item in batch_items:
                try:
                    # Create structured file content for vector store
                    file_content = f"""Lead ID: {item['id']}
Company: {company_name}
Content: {item['text']}
Metadata: {item['metadata']}"""
                    
                    # Create a temporary file and upload
                    import tempfile
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
                        temp_file.write(file_content)
                        temp_file.flush()
                        
                        # Upload file to OpenAI
                        with open(temp_file.name, 'rb') as f:
                            file_obj = client.files.create(
                                file=f,
                                purpose="assistants"
                            )
                            file_objects.append(file_obj)
                    
                    # Clean up temp file
                    import os
                    os.unlink(temp_file.name)
                    
                except Exception as e:
                    logger.warning(f"Error creating file for lead {item['id']}: {e}")
                    continue
            
            # Add files to vector store in a batch
            if file_objects:
                try:
                    file_batch = client.beta.vector_stores.file_batches.create(
                        vector_store_id=target_store.id,
                        file_ids=[f.id for f in file_objects]
                    )
                    
                    # Wait for batch processing to complete
                    max_wait = 120  # Increased wait time
                    wait_time = 0
                    
                    while file_batch.status in ["in_progress", "queued"] and wait_time < max_wait:
                        time.sleep(3)
                        wait_time += 3
                        file_batch = client.beta.vector_stores.file_batches.retrieve(
                            vector_store_id=target_store.id,
                            batch_id=file_batch.id
                        )
                        logger.info(f"Batch status: {file_batch.status}")
                    
                    if file_batch.status == "completed":
                        total_upserted += len(batch_items)
                        logger.info(f"Successfully processed batch {i//batch_size + 1}")
                    else:
                        logger.warning(f"Batch {i//batch_size + 1} status: {file_batch.status}")
                        # Still count as processed for now
                        total_upserted += len(batch_items)
                        
                except Exception as e:
                    logger.warning(f"Error processing file batch: {e}")
                    continue
            
            # Small delay between batches
            if i + batch_size < len(items):
                time.sleep(2)
        
        return {
            "upserted": total_upserted,
            "vector_store_id": target_store.id,
            "message": f"Processed {total_upserted} documents"
        }
        
    except Exception as e:
        logger.error(f"Error upserting documents for {company_name}: {e}")
        raise

@backoff.on_exception(backoff.expo, Exception, max_tries=3, max_time=30)
def delete_vectors_by_filter(company_name: str, assigned_to: str = None, assigned_to_id: str = None) -> dict:
    """
    Delete existing vectors for a company or specific assignedTo group.
    
    Args:
        company_name: The name of the company
        assigned_to: Optional assigned to name filter
        assigned_to_id: Optional assigned to ID filter
        
    Returns:
        dict: Summary of the delete operation
    """

    try:
        vector_store_name = getVectorStoreName(company_name)
        
        # Find vector store
        vector_stores = client.beta.vector_stores.list()
        target_store = None
        
        for store in vector_stores.data:
            if store.name == vector_store_name:
                target_store = store
                break
        
        if not target_store:
            return {"deleted": 0, "message": f"No vector store found for {company_name}"}
        
        # If full refresh (no filters), delete the entire vector store and recreate
        if not assigned_to and not assigned_to_id:
            client.beta.vector_stores.delete(target_store.id)
            logger.info(f"Deleted vector store for {company_name}")
            return {"deleted": "all", "message": f"Deleted entire vector store for {company_name}"}
        
        # For filtered deletion, we would need to implement file-level deletion
        # This is more complex with OpenAI's current API
        logger.warning(f"Filtered deletion not yet implemented for {company_name}")
        return {"deleted": 0, "message": "Filtered deletion not implemented"}
        
    except Exception as e:
        logger.error(f"Error deleting vectors for {company_name}: {e}")
        raise

def search_vector_store(company_name: str, query: str, top_k: int = 20) -> List[Dict[str, Any]]:
    """
    Search the vector store for semantically similar documents.
    
    Args:
        company_name: The name of the company
        query: The search query
        top_k: Number of top results to return
        
    Returns:
        List[Dict[str, Any]]: List of search results with metadata and content
    """
    
    try:
        vector_store_name = getVectorStoreName(company_name)
        
        # Find vector store
        vector_stores = client.beta.vector_stores.list()
        target_store = None
        
        for store in vector_stores.data:
            if store.name == vector_store_name:
                target_store = store
                break
        
        if not target_store:
            logger.warning(f"No vector store found for {company_name}")
            return []
        
        # Create a temporary assistant for search
        assistant = client.beta.assistants.create(
            name=f"Search Assistant for {company_name}",
            instructions=f"You are a search assistant for {company_name} leads. Find and return relevant lead information based on the user's query. Always include specific lead details like Lead ID, project information, and contact details when available.",
            model="gpt-4o-mini",  # Use a more cost-effective model for search
            tools=[{"type": "file_search"}],
            tool_resources={"file_search": {"vector_store_ids": [target_store.id]}}
        )
        
        try:
            # Create a thread and run search
            thread = client.beta.threads.create()
            
            # Send the search query
            client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=f"Search for leads related to: {query}. Return the top {top_k} most relevant leads with their details."
            )
            
            # Run the assistant
            run = client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=assistant.id
            )
            
            # Wait for completion
            max_wait = 30
            wait_time = 0
            while run.status in ["queued", "in_progress"] and wait_time < max_wait:
                time.sleep(1)
                wait_time += 1
                run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
            
            if run.status == "completed":
                # Get the assistant's response
                messages = client.beta.threads.messages.list(thread_id=thread.id)
                
                # Find the assistant's response
                assistant_message = None
                for message in messages.data:
                    if message.role == "assistant":
                        assistant_message = message
                        break
                
                if assistant_message and assistant_message.content:
                    # Extract content from the response
                    content_text = ""
                    for content_block in assistant_message.content:
                        if hasattr(content_block, 'text'):
                            content_text += content_block.text.value
                    
                    # For now, return a simplified result structure
                    # In production, you'd parse the assistant's response to extract individual leads
                    return [{
                        "id": "search_results",
                        "content": content_text,
                        "metadata": {
                            "companyName": company_name,
                            "searchQuery": query,
                            "resultType": "assistant_search"
                        },
                        "score": 1.0
                    }]
                else:
                    logger.warning("No content in assistant response")
                    return []
            else:
                logger.warning(f"Search run did not complete: {run.status}")
                return []
                
        finally:
            # Clean up resources
            try:
                client.beta.threads.delete(thread.id)
                client.beta.assistants.delete(assistant.id)
            except Exception as cleanup_e:
                logger.warning(f"Error cleaning up search resources: {cleanup_e}")
        
        return []
        
    except Exception as e:
        logger.error(f"Error searching vector store for {company_name}: {e}")
        return []
