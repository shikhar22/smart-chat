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
from flatten_utils import flattenLeadToText
from vectorstore_utils import (
    getVectorStoreName, 
    fetch_existing_metadata_map, 
    embed_texts, 
    upsert_lead_documents,
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
    print("Success!!!!!")
    print(client)
except Exception as e:
    logger.warning(f"OpenAI client initialization warning: {e}")
    client = None

# Pydantic models for request/response
class UpdateLeadsRequest(BaseModel):
    """Request model for updating leads in vector store."""
    companyName: str = Field(..., min_length=1, description="The name of the company")
    assignedTo: Optional[str] = Field(None, description="Filter by assigned to name")
    assignedToId: Optional[str] = Field(None, description="Filter by assigned to ID") 
    forceRefresh: bool = Field(False, description="Force refresh all leads")

class UpdateLeadsResponse(BaseModel):
    """Response model for update leads operation."""
    companyName: str
    totalLeadsFetched: int
    totalUpserted: int
    totalSkipped: int

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

@app.post("/update-leads", response_model=UpdateLeadsResponse)
async def update_leads(request: UpdateLeadsRequest):
    """
    Fetch leads from company-specific Firebase, flatten, embed, and upsert to OpenAI Vector Store.
    
    Steps:
    1. Initialize Firebase app for the company
    2. Fetch all leads from Firebase
    3. Optionally filter leads by assignedTo/assignedToId
    4. Check existing metadata to determine which leads need updating
    5. Flatten leads to text and prepare for embedding
    6. Batch embed and upsert to vector store
    7. Return summary
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
        
        # Step 4: Check existing metadata to determine updates needed
        existing_map = fetch_existing_metadata_map(request.companyName) if not request.forceRefresh else {}
        
        leads_to_upsert = []
        for lead in leads:
            lead_id = lead.get('id')
            updated_at = lead.get('updatedAt')
            
            if (lead_id not in existing_map or 
                updated_at != existing_map.get(lead_id) or 
                request.forceRefresh):
                leads_to_upsert.append(lead)
        
        total_skipped = len(leads) - len(leads_to_upsert)
        logger.info(f"Need to upsert {len(leads_to_upsert)} leads, skipping {total_skipped}")
        
        # Step 5: Prepare items for embedding and upserting
        items = []
        for lead in leads_to_upsert:
            try:
                # Flatten lead to text
                text = flattenLeadToText(lead, request.companyName)
                
                # Prepare metadata in camelCase
                metadata = {
                    "companyName": request.companyName,
                    "assignedTo": lead.get('assignedTo', ''),
                    "assignedToId": lead.get('assignedToId', ''),
                    "updatedAt": lead.get('updatedAt', ''),
                    "projectCity": lead.get('projectCity', ''),
                    "projectCategory": lead.get('projectCategory', ''),
                    "id": lead.get('id', ''),
                    "generatedAt": lead.get('generatedAt', ''),
                    "projectStage": lead.get('projectStage', ''),
                    "projectSource": lead.get('projectSource', '')
                }
                
                # Remove empty values from metadata
                metadata = {k: v for k, v in metadata.items() if v}
                
                items.append({
                    "id": lead.get('id', ''),
                    "text": text,
                    "metadata": metadata
                })
                
            except Exception as e:
                logger.warning(f"Error processing lead {lead.get('id', 'unknown')}: {e}")
                continue
        
        # Step 6: Upsert to vector store
        total_upserted = 0
        if items:
            upsert_result = upsert_lead_documents(request.companyName, items)
            total_upserted = upsert_result.get('upserted', 0)
            logger.info(f"Upserted {total_upserted} leads to vector store")
        
        # Step 7: Return summary
        return UpdateLeadsResponse(
            companyName=request.companyName,
            totalLeadsFetched=total_leads_fetched,
            totalUpserted=total_upserted,
            totalSkipped=total_skipped
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
        search_results = search_vector_store(request.companyName, request.question, top_k=10)
        
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
            
            # Extract key metadata for display
            lead_id = metadata.get('id', f'doc_{i}')
            project_city = metadata.get('projectCity', 'Unknown')
            updated_at = metadata.get('updatedAt', 'Unknown')
            
            doc_summary = f"Lead ID: {lead_id}, City: {project_city}, Updated: {updated_at}"
            docs_context.append(f"Document {i+1}: {doc_summary}\nContent: {content}\n")
            
            sources.append({
                "id": lead_id,
                "score": result.get('score', 0.0),
                "metadata": metadata,
                "snippet": content[:200] + "..." if len(content) > 200 else content
            })
        
        rag_prompt = f"""You are a sales analyst. User question: {request.question}

Here are the top relevant leads (metadata + content):

{''.join(docs_context)}

Please answer the user's question concisely and include numeric comparisons (e.g., % change, counts) where applicable. If specific data is missing, say so clearly. 

Structure your response with these sections when relevant:
- Lead Volume & Trends
- Engagement & Follow-ups  
- Source & Quality
- Stakeholder Activity
- Smart Observations
- Final Summary with actionable recommendations

Focus on being analytical and data-driven in your response."""
        
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

if __name__ == "__main__":
    # Check for required environment variables
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY environment variable is required")
        exit(1)
    
    uvicorn.run(app, host="0.0.0.0", port=8008)
