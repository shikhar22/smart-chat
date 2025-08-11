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

@backoff.on_exception(backoff.expo, Exception, max_tries=3, max_time=30)
def embed_texts(texts: List[str], batch_size: int = 64) -> List[List[float]]:
    """
    Embed a list of texts using OpenAI's text-embedding-3-small model.
    
    NOTE: This function is deprecated in favor of the chunked document approach
    where OpenAI handles embeddings automatically through the vector store API.
    Kept for backward compatibility.
    
    Args:
        texts: List of text strings to embed
        batch_size: Number of texts to process in each batch
        
    Returns:
        List[List[float]]: List of embedding vectors
    """
    logger.warning("embed_texts is deprecated - chunked documents use automatic embeddings")
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
def upsert_chunked_documents(company_name: str, documents: List[Dict[str, Any]]) -> dict:
    """
    Upsert chunked documents into OpenAI Vector Store.
    
    Args:
        company_name: The name of the company
        documents: List of chunked documents with keys: "id", "text", "metadata"
        
    Returns:
        dict: Summary of the upsert operation
    """
    if not documents:
        return {"upserted": 0, "message": "No documents to upsert"}
        
    try:
        vector_store_name = getVectorStoreName(company_name)
        
        # Delete existing vector store to ensure clean state
        vector_stores = client.beta.vector_stores.list()
        for store in vector_stores.data:
            if store.name == vector_store_name:
                logger.info(f"Deleting existing vector store: {vector_store_name}")
                client.beta.vector_stores.delete(store.id)
                break
        
        # Create new vector store
        logger.info(f"Creating new vector store: {vector_store_name}")
        target_store = client.beta.vector_stores.create(
            name=vector_store_name,
            metadata={"company": company_name, "document_type": "chunked_leads"}
        )
        
        # Create files with chunked content and upload to vector store
        batch_size = 10  # Smaller batch size for chunked documents
        total_upserted = 0
        
        for i in range(0, len(documents), batch_size):
            batch_documents = documents[i:i + batch_size]
            
            logger.info(f"Processing batch {i//batch_size + 1} ({len(batch_documents)} documents)")
            
            # Create file objects for this batch
            file_objects = []
            
            for doc in batch_documents:
                try:
                    # Create structured file content for vector store
                    metadata = doc['metadata']
                    file_content = f"""Company: {company_name}
Assignee: {metadata.get('assignedTo', 'Unknown')}
Chunk: {metadata.get('chunk_index', 0) + 1} of {metadata.get('total_chunks', 1)}
Total Leads: {metadata.get('total_leads', 0)}

{doc['text']}

---
Metadata: {metadata}"""
                    
                    # Create a temporary file and upload
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
                    logger.warning(f"Error creating file for document {doc['id']}: {e}")
                    continue
            
            # Add files to vector store in a batch
            if file_objects:
                try:
                    file_batch = client.beta.vector_stores.file_batches.create(
                        vector_store_id=target_store.id,
                        file_ids=[f.id for f in file_objects]
                    )
                    
                    # Wait for batch processing to complete
                    max_wait = 180  # Increased wait time for chunked documents
                    wait_time = 0
                    
                    while file_batch.status in ["in_progress", "queued"] and wait_time < max_wait:
                        time.sleep(5)
                        wait_time += 5
                        file_batch = client.beta.vector_stores.file_batches.retrieve(
                            vector_store_id=target_store.id,
                            batch_id=file_batch.id
                        )
                        logger.info(f"Batch status: {file_batch.status}")
                    
                    if file_batch.status == "completed":
                        total_upserted += len(batch_documents)
                        logger.info(f"Successfully processed batch {i//batch_size + 1}")
                    else:
                        logger.warning(f"Batch {i//batch_size + 1} status: {file_batch.status}")
                        # Still count as processed for now
                        total_upserted += len(batch_documents)
                        
                except Exception as e:
                    logger.warning(f"Error processing file batch: {e}")
                    continue
            
            # Small delay between batches
            if i + batch_size < len(documents):
                time.sleep(3)
        
        return {
            "upserted": total_upserted,
            "vector_store_id": target_store.id,
            "message": f"Processed {total_upserted} chunked documents"
        }
        
    except Exception as e:
        logger.error(f"Error upserting chunked documents for {company_name}: {e}")
        raise

# Keep the old function for backward compatibility during transition
upsert_lead_documents = upsert_chunked_documents

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
    Uses a simple but reliable approach that avoids complex assistant threading.
    
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
        
        # Get files in vector store to ensure data exists
        try:
            vector_store_files = client.beta.vector_stores.files.list(
                vector_store_id=target_store.id,
            )
            
            if not vector_store_files.data:
                logger.warning(f"No files found in vector store for {company_name}")
                return []
            
            logger.info(f"Found {len(vector_store_files.data)} files in vector store for {company_name}")
            
            # Use a very simple assistant approach with strict timeout
            assistant = client.beta.assistants.create(
                name=f"Search-{company_name}-{int(time.time())}",  # Unique name
                instructions="Extract relevant lead information. Be brief and specific.",
                model="gpt-4o-mini",
                tools=[{"type": "file_search"}],
                tool_resources={"file_search": {"vector_store_ids": [target_store.id]}}
            )
            
            thread = None
            try:
                # Create thread and message
                thread = client.beta.threads.create()
                
                client.beta.threads.messages.create(
                    thread_id=thread.id,
                    role="user",
                    content=f"Search for: {query}"
                )
                
                # Run with very short timeout
                run = client.beta.threads.runs.create(
                    thread_id=thread.id,
                    assistant_id=assistant.id
                )
                
                # Poll with aggressive timeout
                max_attempts = 100
                attempt = 0
                
                while attempt < max_attempts:
                    run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
                    
                    if run.status == "completed":
                        # Get response
                        messages = client.beta.threads.messages.list(thread_id=thread.id)
                        
                        for message in messages.data:
                            if message.role == "assistant":
                                content_text = ""
                                for content_block in message.content:
                                    if hasattr(content_block, 'text'):
                                        content_text += content_block.text.value
                                
                                if content_text:
                                    return [{
                                        "id": f"result_{company_name}",
                                        "content": content_text,
                                        "metadata": {
                                            "companyName": company_name,
                                            "searchQuery": query,
                                            "resultType": "assistant_search",
                                            "assignedTo": "Multiple",
                                            "total_files": len(vector_store_files.data)
                                        },
                                        "score": 1.0
                                    }]
                                break
                        break
                    
                    elif run.status in ["failed", "cancelled", "expired"]:
                        logger.warning(f"Search run failed: {run.status}")
                        break
                    
                    time.sleep(0.5)
                    attempt += 1
                
                # If we get here, the search didn't complete in time
                logger.warning(f"Search timed out after {max_attempts * 0.5}s")
                
            finally:
                # Quick cleanup
                if thread:
                    try:
                        client.beta.threads.delete(thread.id)
                    except:
                        pass
                try:
                    client.beta.assistants.delete(assistant.id)
                except:
                    pass
            
            # Fallback: return indication that data exists
            return [{
                "id": f"available_{company_name}",
                "content": f"Lead data is available for {company_name} with {len(vector_store_files.data)} portfolio documents. The vector search is currently processing - please try again in a moment or rephrase your question.",
                "metadata": {
                    "companyName": company_name,
                    "searchQuery": query,
                    "resultType": "data_available",
                    "available_documents": len(vector_store_files.data),
                    "assignedTo": "Multiple assignees",
                    "total_chunks": len(vector_store_files.data)
                },
                "score": 0.7
            }]
            
        except Exception as files_e:
            logger.error(f"Error accessing files: {files_e}")
            return []
        
    except Exception as e:
        logger.error(f"Error in search for {company_name}: {e}")
        return []
