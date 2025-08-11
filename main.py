#!/usr/bin/env python3
"""
FastAPI application for semantic RAG pipeline with lead processing.
Provides exactly two endpoints: /update-leads and /ask.
"""

import logging
import os
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
from openai import OpenAI

# Import our utility modules
from firebase_utils import init_firebase_app, fetch_all_leads
from chunking_utils import group_leads_by_assignee, create_chunked_documents
from vectorstore_utils import (
    getVectorStoreName, 
    upsert_chunked_documents,
    delete_vectors_by_filter,
    search_vector_store
)
from dotenv import load_dotenv

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI client with graceful handling
try:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
except Exception as e:
    logger.warning(f"OpenAI client initialization warning: {e}")
    client = None

# Pydantic models for request/response
class UpdateLeadsRequest(BaseModel):
    """Request model for updating leads in vector store."""
    companyName: str = Field(..., min_length=1, description="The name of the company")
    assignedTo: Optional[str] = Field(None, description="Filter by assigned to name")
    assignedToId: Optional[str] = Field(None, description="Filter by assigned to ID")

class UpdateLeadsResponse(BaseModel):
    """Response model for update leads operation."""
    companyName: str
    totalLeadsFetched: int
    totalAssignees: int
    totalDocumentsCreated: int
    assigneeBreakdown: Dict[str, int]

class AskRequest(BaseModel):
    """Request model for asking questions using RAG."""
    companyName: str = Field(..., min_length=1, description="The name of the company")
    question: str = Field(..., min_length=1, description="The natural language question")

class AskResponse(BaseModel):
    """Response model for ask operation."""
    answer: str
    sources: List[Dict[str, Any]]

# Initialize FastAPI app
app = FastAPI(
    title="Semantic RAG Pipeline API",
    description="API for lead processing and semantic question answering",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Optional, delete the vector store
# @app.post("/delete-vector-store", response_model=UpdateLeadsResponse)
# async def delete_vector_store(request: UpdateLeadsRequest):
#     print("Starting deletion of vectors...")
#     response = delete_vectors_by_filter(request.companyName)
#     print(response)

@app.post("/update-leads", response_model=UpdateLeadsResponse)
async def update_leads(request: UpdateLeadsRequest):
    """
    Fetch leads from company-specific Firebase, group by assignee, chunk optimally, and upsert to OpenAI Vector Store.
    
    Steps:
    1. Initialize Firebase app for the company
    2. Fetch all leads from Firebase
    3. Optionally filter leads by assignedTo/assignedToId
    4. Group leads by assignee
    5. Create chunked documents for each assignee group
    6. Upsert chunked documents to vector store
    7. Return summary with assignee breakdown
    """
    try:
        logger.info(f"Processing update-leads request for company: {request.companyName}")
        
        # Step 1: Initialize Firebase app
        init_firebase_app(request.companyName)
        
        # Step 2: Fetch all leads
        leads = fetch_all_leads(request.companyName)
        total_leads_fetched = len(leads)
        
        logger.info(f"Fetched {total_leads_fetched} leads for {request.companyName}")
        
        # Step 3: Filter leads if assignedTo or assignedToId provided
        if request.assignedTo or request.assignedToId:
            filtered_leads = []
            for lead in leads:
                assigned_to_match = True
                assigned_to_id_match = True
                
                if request.assignedTo:
                    assigned_to_match = lead.get('assignedTo') == request.assignedTo
                
                if request.assignedToId:
                    assigned_to_id_match = lead.get('assignedToId') == request.assignedToId
                
                if assigned_to_match and assigned_to_id_match:
                    filtered_leads.append(lead)
            
            leads = filtered_leads
            logger.info(f"Filtered to {len(leads)} leads based on assignedTo/assignedToId")
        
        if not leads:
            logger.warning(f"No leads found for {request.companyName} after filtering")
            return UpdateLeadsResponse(
                companyName=request.companyName,
                totalLeadsFetched=total_leads_fetched,
                totalAssignees=0,
                totalDocumentsCreated=0,
                assigneeBreakdown={}
            )
        
        # Step 4: Group leads by assignee
        grouped_leads = group_leads_by_assignee(leads)
        
        # Step 5: Create chunked documents for each assignee group
        chunked_documents = create_chunked_documents(grouped_leads, request.companyName)
        
        # Create assignee breakdown
        assignee_breakdown = {}
        for assignee, assignee_leads in grouped_leads.items():
            assignee_breakdown[assignee] = len(assignee_leads)
        
        # Step 6: Upsert chunked documents to vector store
        total_documents_created = 0
        if chunked_documents:
            upsert_result = upsert_chunked_documents(request.companyName, chunked_documents)
            total_documents_created = upsert_result.get('upserted', 0)
            logger.info(f"Upserted {total_documents_created} chunked documents to vector store")
        
        # Step 7: Return summary
        return UpdateLeadsResponse(
            companyName=request.companyName,
            totalLeadsFetched=total_leads_fetched,
            totalAssignees=len(grouped_leads),
            totalDocumentsCreated=total_documents_created,
            assigneeBreakdown=assignee_breakdown
        )
        
    except FileNotFoundError as e:
        logger.error(f"Firebase configuration not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error in update-leads: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/ask", response_model=AskResponse)
async def ask_question(request: AskRequest):
    """
    Retrieve top 10 semantically relevant lead docs and answer using GPT-4o (RAG).
    
    Steps:
    1. Get vector store name for the company
    2. Search vector store for semantically similar documents
    3. Build RAG prompt with retrieved documents
    4. Call GPT-4o with the RAG prompt
    5. Return answer and sources
    """
    try:
        logger.info(f"Processing ask request for company: {request.companyName}")
        
        # Step 1 & 2: Search vector store
        vector_store_name = getVectorStoreName(request.companyName)
        search_results = search_vector_store(request.companyName, request.question, top_k=20)
        
        if not search_results:
            logger.warning(f"No search results found for {request.companyName}")
            return AskResponse(
                answer="I don't have any lead data available for this company in the vector store. Please ensure leads have been processed using the /update-leads endpoint first.",
                sources=[]
            )
        
        # Step 3: Build RAG prompt
        docs_context = []
        sources = []
        
        for i, result in enumerate(search_results[:10]):
            metadata = result.get('metadata', {})
            content = result.get('content', '')
            
            # Extract key metadata for display (adapted for chunked documents)
            assignee = metadata.get('assignedTo', 'Unknown')
            chunk_info = f"chunk {metadata.get('chunk_index', 0) + 1}/{metadata.get('total_chunks', 1)}"
            total_leads = metadata.get('total_leads', 'Unknown')
            
            doc_summary = f"Assignee: {assignee}, {chunk_info}, Total Leads: {total_leads}"
            docs_context.append(f"Document {i+1}: {doc_summary}\nContent: {content}\n")
            
            sources.append({
                "assignee": assignee,
                "chunk_index": metadata.get('chunk_index', 0),
                "total_chunks": metadata.get('total_chunks', 1),
                "total_leads": metadata.get('total_leads', 0),
                "score": result.get('score', 0.0),
                "metadata": metadata,
                "snippet": content[:300] + "..." if len(content) > 300 else content
            })
        
        rag_prompt = f"""You are a sales analyst working with grouped lead data. User question: {request.question}

Here are the top relevant lead portfolios (each document contains multiple leads grouped by assignee):

{''.join(docs_context)}

Please answer the user's question concisely and include numeric comparisons (e.g., % change, counts) where applicable. If specific data is missing, say so clearly. 

Structure your response with these sections when relevant:
- Lead Volume & Trends (by assignee)
- Engagement & Follow-ups  
- Source & Quality
- Stakeholder Activity
- Smart Observations
- Final Summary with actionable recommendations

Focus on being analytical and data-driven in your response. Note that each document represents a portfolio of leads for a specific assignee."""
        
        # Step 4: Call GPT-4o
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a helpful sales analyst assistant."},
                    {"role": "user", "content": rag_prompt}
                ],
                temperature=0.3,  # Lower temperature for more consistent analytical responses
                max_tokens=1500
            )
            
            answer = response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error calling GPT-4o: {e}")
            # Fallback to GPT-3.5-turbo if GPT-4o fails
            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a helpful sales analyst assistant."},
                        {"role": "user", "content": rag_prompt}
                    ],
                    temperature=0.3,
                    max_tokens=1500
                )
                answer = response.choices[0].message.content
            except Exception as fallback_e:
                logger.error(f"Error with fallback model: {fallback_e}")
                raise HTTPException(status_code=500, detail="Error generating response from AI model")
        
        # Step 5: Return response
        return AskResponse(
            answer=answer,
            sources=sources
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in ask endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/")
async def root():
    """Root endpoint - health check."""
    return {
        "message": "Semantic RAG Pipeline API is running",
        "endpoints": ["/update-leads", "/ask"],
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "API is operational"}

@app.get("/vector-store-status/{company_name}")
async def vector_store_status(company_name: str):
    """Check if vector store exists and has data for a company."""
    try:
        from vectorstore_utils import getVectorStoreName
        
        vector_store_name = getVectorStoreName(company_name)
        
        # Find vector store
        vector_stores = client.beta.vector_stores.list()
        target_store = None
        
        for store in vector_stores.data:
            if store.name == vector_store_name:
                target_store = store
                break
        
        if not target_store:
            return {
                "company": company_name,
                "vector_store_exists": False,
                "file_count": 0,
                "status": "no_data"
            }
        
        # Get file count
        vector_store_files = client.beta.vector_stores.files.list(
            vector_store_id=target_store.id,
            limit=100
        )
        
        return {
            "company": company_name,
            "vector_store_exists": True,
            "vector_store_id": target_store.id,
            "file_count": len(vector_store_files.data),
            "status": "ready" if len(vector_store_files.data) > 0 else "empty"
        }
        
    except Exception as e:
        logger.error(f"Error checking vector store status for {company_name}: {e}")
        return {
            "company": company_name,
            "vector_store_exists": False,
            "file_count": 0,
            "status": "error",
            "error": str(e)
        }

if __name__ == "__main__":
    # Check for required environment variables
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY environment variable is required")
        exit(1)
    
    uvicorn.run(app, host="0.0.0.0", port=8008)
