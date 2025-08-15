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
from chunking_utils import create_chunked_documents
from vectorstore import getVectorStoreName, upsert_chunked_documents, vector_store_search
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
    totalDocumentsCreated: int

class AskRequest(BaseModel):
    """Request model for asking questions using RAG."""
    companyName: str = Field(..., min_length=1, description="The name of the company")
    question: str = Field(..., min_length=1, description="The natural language question")

class AskResponse(BaseModel):
    """Response model for ask operation."""
    answer: str

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
                totalDocumentsCreated=0,
            )
        
        # Create chunked documents for each lead
        chunked_documents = create_chunked_documents(leads, request.companyName)

        # Upsert chunked documents to vector store
        total_documents_created = 0
        if chunked_documents:
            upsert_result = upsert_chunked_documents(request.companyName, chunked_documents)
            logger.info(f"Upsert Result {upsert_result}")
        
        return UpdateLeadsResponse(
            companyName=request.companyName,
            totalLeadsFetched=total_leads_fetched,
            totalDocumentsCreated=total_documents_created,
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
    5. Return answer
    """
    try:
        logger.info(f"Processing ask request for company: {request.companyName}")

        search_results = vector_store_search(request.companyName, request.question)
        
        if not search_results:
            logger.warning(f"No search results found for {request.companyName}")
            return AskResponse(
                answer="I don't have any lead data available for this company in the vector store. Please ensure leads have been processed using the /update-leads endpoint first.",
            )
        
        rag_prompt = f"""You are a sales analyst working with grouped lead data. User question: {request.question}

            Here are the top relevant lead portfolios (each document contains multiple leads grouped by assignee):

            {search_results}

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

if __name__ == "__main__":
    # Check for required environment variables
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY environment variable is required")
        exit(1)
    
    uvicorn.run(app, host="0.0.0.0", port=8008)
