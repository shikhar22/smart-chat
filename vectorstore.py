import os
import logging
import backoff
from typing import List, Dict, Any
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
logger = logging.getLogger(__name__)

try:
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    api_key = os.getenv("OPENAI_API_KEY")
    if not PINECONE_API_KEY or not api_key:
        logger.error("PINECONE_API_KEY or OPENAI_API_KEY environment variable is not set")
    else:
        # Initialize with basic parameters only
        pc = Pinecone(api_key=PINECONE_API_KEY)
        client = OpenAI(api_key=api_key)
        logger.info("Pinecone initialized successfully")
except Exception as e:
    logger.error(f"Pinecone initialization failed: {e}")

def getVectorStoreName(company_name: str) -> str:
    """
    Generate a standardized vector store name for a company.
    
    Args:
        company_name: The name of the company
        
    Returns:
        str: The vector store name (e.g., "kalco_leads")
    """
    if(company_name == 'none'):
        return 'default'

    return f"{company_name.lower()}-leads"

def embed_text(text):
    return client.embeddings.create(
        model="text-embedding-3-large",
        input=text
    ).data[0].embedding

@backoff.on_exception(backoff.expo, Exception, max_tries=3, max_time=60)
def upsert_chunked_documents(company_name: str, documents: List[Dict[str, Any]], batch_size: int = 95) -> dict:
    """
    Upsert chunked documents into the vector store in batches.

    Args:
        company_name: The name of the company
        documents: The list of chunked documents to upsert
        batch_size: Number of documents to process in each batch (default: 100)

    Returns:
        dict: The result of the upsert operation with total upserted count
    """
    vector_store_name = getVectorStoreName(company_name)
    if vector_store_name == 'default':
        return {"upserted": 0}

    if not pc.has_index(vector_store_name):
        pc.create_index(
            name=vector_store_name,
            dimension=3072,
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            ),
        )
    
    index = pc.Index(vector_store_name)
    total_upserted = 0

    # Process documents in batches
    try:
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}: {len(batch)} documents")

            texts = []
            metadatas = []
            ids = []
            
            for rec in batch:
                text = rec['chunk_text']
                metadata = rec['metadata']
                texts.append(text)
                metadatas.append(metadata)
                ids.append(rec['id'])

            embeddings = client.embeddings.create(
                model="text-embedding-3-large",
                input=texts
            ).data

            vectors = []
            for j, emb in enumerate(embeddings):
                vectors.append({
                    "id": ids[j],
                    "values": emb.embedding,
                    "metadata": metadatas[j]
                })

            response = index.upsert(vectors=vectors)
            
            # response = index.upsert_records(company_name, batch)
            if hasattr(response, 'upserted_count'):
                total_upserted += response.upserted_count
            else:
                total_upserted += len(batch)
            
            logger.info(f"Batch {i//batch_size + 1} completed successfully")
        
        return {"upserted": total_upserted, "total_batches": (len(documents) + batch_size - 1) // batch_size}
    except Exception as e:
        logger.error(f"Error upserting documents to {vector_store_name}: {e}")
        return {"upserted": total_upserted}

def extract_filters_from_query(user_query):
    system_prompt = """
    You are a parser that extracts structured search filters from user queries
    for a construction project database. 
    Output must be valid JSON with two fields:
    - semantic_query: string (for semantic search)
    - filters: dict of Pinecone metadata filters.
    
    Supported metadata keys:
    - assignedTo, city, state, projectStage, concernPerson, projectCategory, leadSource, priority, status, phone, email (string fields)
    - createdAt, updatedAt (Unix timestamp fields)

    For date filters, convert dates to Unix timestamps before using $gte or $lte operators.
    String matches can use $eq for exact match.

    For current month's date take only $gte
    
    Examples:
    - "projects from July 2025" -> {
        "semantic_query": "projects from July 2025",
        "filters": {
            "createdAt": {
                "$gte": 1751328000,
                "$lte": 1754006399
            }
        }
    }
    - "assigned to John" -> {
        "semantic_query": "assigned to John",
        "filters": {"assignedTo": {"$eq": "John"}}
    }
    - "projects in California" -> {
        "semantic_query": "projects in California",
        "filters": {"state": {"$eq": "California"}}
    }
    """

    resp = client.chat.completions.create(
        model=os.getenv("GPT_Model"),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Query: {user_query}"}
        ],
        temperature=0
    )

    import json
    try:
        parsed = json.loads(resp.choices[0].message.content)
    except json.JSONDecodeError:
        parsed = {"semantic_query": user_query, "filters": {}}
    return parsed

@backoff.on_exception(backoff.expo, Exception, max_tries=3, max_time=60)
def vector_store_search(company_name: str, query: str, top_k: int = 30) -> List[Dict[str, Any]]:
    """
    Perform semantic search on the vector store to find relevant documents.

    Args:
        company_name: The name of the company
        query: The search query text
        top_k: Number of top results to return (default: 30)

    Returns:
        List[Dict[str, Any]]: List of matching documents with scores
    """


    vector_store_name = getVectorStoreName(company_name)
    if vector_store_name == 'default':
        logger.warning("Cannot search default vector store")
        return []

    # Check if index exists
    if not pc.has_index(vector_store_name):
        logger.warning(f"Vector store {vector_store_name} does not exist")
        return []

    try:
        index = pc.Index(vector_store_name)

        parsed = extract_filters_from_query(query)
        semantic_query = parsed["semantic_query"]
        metadata_filter = parsed["filters"]

        print("Semantic query:", semantic_query)
        print("Metadata filter:", metadata_filter)

        query_emb = embed_text(semantic_query)

        results = index.query(
            vector=query_emb,
            top_k=top_k,
            include_metadata=True,
            filter=metadata_filter if metadata_filter else None
        )

        context = "\n\n".join([
            f"Project ID: {match['id']}\nMetadata: {match['metadata']}"
            for match in results["matches"]
        ])

        return context
        
    except Exception as e:
        logger.error(f"Error searching vector store {vector_store_name}: {e}")
        return []

