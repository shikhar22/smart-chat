#!/usr/bin/env python3
"""
FastAPI application for AI Chat Agent
Provides REST API endpoints to interact with the AI agent.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uvicorn
from agent import BasicAIAgent
from rag_agent import CompanyRAGAgent
from firebase_client import fetch_company_leads, validate_firebase_company

# Pydantic models for request/response
class QuestionRequest(BaseModel):
    """Request model for asking a question."""
    question: str = Field(..., min_length=1, description="The question to ask the AI agent")
    model_name: Optional[str] = Field("gpt-3.5-turbo", description="OpenAI model to use")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=1.0, description="Temperature for response randomness")

class CompanyQuestionRequest(BaseModel):
    """Request model for asking a company-specific question using RAG."""
    question: str = Field(..., min_length=1, description="The question to ask about the company")
    company_name: str = Field(..., min_length=1, description="The name of the company to ask about")
    model_name: Optional[str] = Field("gpt-3.5-turbo", description="OpenAI model to use")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=1.0, description="Temperature for response randomness")

class AddDocumentRequest(BaseModel):
    """Request model for adding a company document."""
    company_name: str = Field(..., min_length=1, description="The name of the company")
    content: str = Field(..., min_length=1, description="The content of the document")
    filename: str = Field(..., min_length=1, description="The filename for the document")

class UpdateDataRequest(BaseModel):
    """Request model for updating company data from Firebase."""
    company: str = Field(..., min_length=1, description="The name of the company to fetch data for")

class UpdateDataResponse(BaseModel):
    """Response model for update data operation."""
    status: str
    message: str
    company: str
    leads_count: int
    leads: List[Dict[str, Any]]

class QuestionResponse(BaseModel):
    """Response model for question answers."""
    question: str
    answer: str
    model_used: str
    temperature: float

class CompanyQuestionResponse(BaseModel):
    """Response model for company-specific question answers."""
    question: str
    answer: str
    company_name: str
    model_used: str
    temperature: float

class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    message: str

class CompaniesResponse(BaseModel):
    """Response model for listing companies."""
    companies: List[str]
    count: int

# Initialize FastAPI app
app = FastAPI(
    title="AI Chat Agent API",
    description="A REST API for interacting with an AI chat agent powered by LangChain and OpenAI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global agent instances
agent_instance = None
rag_agent_instance = None

def get_agent(model_name: str = "gpt-3.5-turbo", temperature: float = 0.7) -> BasicAIAgent:
    """Get or create an AI agent instance."""
    global agent_instance
    try:
        # Create new agent if parameters changed or no agent exists
        if (agent_instance is None or 
            getattr(agent_instance, 'model_name', None) != model_name or
            getattr(agent_instance.llm, 'temperature', None) != temperature):
            agent_instance = BasicAIAgent(model_name=model_name, temperature=temperature)
            # Store model name for comparison
            agent_instance.model_name = model_name
        return agent_instance
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize AI agent: {str(e)}")

def get_rag_agent(model_name: str = "gpt-3.5-turbo", temperature: float = 0.7) -> CompanyRAGAgent:
    """Get or create a RAG agent instance."""
    global rag_agent_instance
    try:
        # Create new agent if parameters changed or no agent exists
        if (rag_agent_instance is None or 
            getattr(rag_agent_instance.llm, 'model_name', None) != model_name or
            getattr(rag_agent_instance.llm, 'temperature', None) != temperature):
            rag_agent_instance = CompanyRAGAgent(model_name=model_name, temperature=temperature)
        return rag_agent_instance
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize RAG agent: {str(e)}")

@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint - health check."""
    return HealthResponse(
        status="healthy",
        message="AI Chat Agent API is running! Visit /docs for API documentation."
    )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        message="AI Chat Agent API is operational"
    )

@app.post("/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    """
    Ask the AI agent a question.
    
    Args:
        request: QuestionRequest containing the question and optional parameters
        
    Returns:
        QuestionResponse with the AI's answer
    """
    try:
        # Get or create agent with specified parameters
        agent = get_agent(model_name=request.model_name, temperature=request.temperature)
        
        # Get response from agent
        answer = agent.ask_question(request.question)
        
        return QuestionResponse(
            question=request.question,
            answer=answer,
            model_used=request.model_name,
            temperature=request.temperature
        )
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")

@app.post("/chat")
async def chat_endpoint(request: QuestionRequest):
    """
    Alternative chat endpoint with simpler response format.
    
    Args:
        request: QuestionRequest containing the question and optional parameters
        
    Returns:
        Simple JSON response with the answer
    """
    try:
        agent = get_agent(model_name=request.model_name, temperature=request.temperature)
        answer = agent.ask_question(request.question)
        
        return {
            "response": answer,
            "status": "success"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in chat: {str(e)}")

@app.post("/ask-company", response_model=CompanyQuestionResponse)
async def ask_company_question(request: CompanyQuestionRequest):
    """
    Ask a question about a specific company using RAG.
    
    Args:
        request: CompanyQuestionRequest containing the question, company name and optional parameters
        
    Returns:
        CompanyQuestionResponse with the AI's answer based on company documents
    """
    try:
        # Get or create RAG agent with specified parameters
        rag_agent = get_rag_agent(model_name=request.model_name, temperature=request.temperature)
        
        # Get response from RAG agent
        answer = rag_agent.ask_company_question(request.question, request.company_name)
        
        return CompanyQuestionResponse(
            question=request.question,
            answer=answer,
            company_name=request.company_name,
            model_used=request.model_name,
            temperature=request.temperature
        )
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing company question: {str(e)}")

@app.get("/companies", response_model=CompaniesResponse)
async def list_companies():
    """
    List all available companies in the knowledge base.
    
    Returns:
        CompaniesResponse with list of company names
    """
    try:
        rag_agent = get_rag_agent()
        companies = rag_agent.list_available_companies()
        
        return CompaniesResponse(
            companies=companies,
            count=len(companies)
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing companies: {str(e)}")

@app.post("/add-company-document")
async def add_company_document(request: AddDocumentRequest):
    """
    Add a document for a specific company to the knowledge base.
    
    Args:
        request: AddDocumentRequest containing company name, content, and filename
        
    Returns:
        Success message
    """
    try:
        rag_agent = get_rag_agent()
        rag_agent.add_company_document(
            company_name=request.company_name,
            content=request.content,
            filename=request.filename
        )
        
        return {
            "status": "success",
            "message": f"Document '{request.filename}' added for company '{request.company_name}'"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding document: {str(e)}")

@app.post("/create-company-vectorstore/{company_name}")
async def create_company_vectorstore(company_name: str, force_recreate: bool = False):
    """
    Create or recreate vector store for a specific company.
    
    Args:
        company_name: Name of the company
        force_recreate: Whether to force recreation of existing vector store
        
    Returns:
        Success message
    """
    try:
        rag_agent = get_rag_agent()
        rag_agent.create_company_vectorstore(company_name, force_recreate=force_recreate)
        
        return {
            "status": "success",
            "message": f"Vector store created for company '{company_name}'"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating vector store: {str(e)}")

@app.post("/update-data", response_model=UpdateDataResponse)
async def update_data(request: UpdateDataRequest):
    """
    Update data for a specific company by fetching leads from Firebase.
    
    Args:
        request: UpdateDataRequest containing the company name
        
    Returns:
        UpdateDataResponse with fetched leads data
    """
    try:
        company_name = request.company
        
        # Validate that the company has Firebase configuration
        if not validate_firebase_company(company_name):
            raise HTTPException(
                status_code=404, 
                detail=f"Firebase configuration not found for company '{company_name}'. "
                       f"Please ensure firebase_config/{company_name}.json exists."
            )
        
        # Fetch leads from Firebase
        leads = fetch_company_leads(company_name)
        
        # TODO: Add downstream processing here
        # For now, we're just returning the fetched data
        
        return UpdateDataResponse(
            status="success",
            message=f"Successfully fetched {len(leads)} leads for company '{company_name}'",
            company=company_name,
            leads_count=len(leads),
            leads=leads
        )
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating data for company '{request.company}': {str(e)}")

@app.get("/models")
async def list_available_models():
    """
    List available OpenAI models that can be used.
    
    Returns:
        List of available model names and API capabilities
    """
    available_models = [
        "gpt-3.5-turbo",
        "gpt-3.5-turbo-16k",
        "gpt-4",
        "gpt-4-turbo-preview",
        "gpt-4o",
        "gpt-4o-mini"
    ]
    
    return {
        "available_models": available_models,
        "default_model": "gpt-3.5-turbo",
        "note": "Model availability depends on your OpenAI API access level",
        "features": {
            "basic_chat": "Available via /ask and /chat endpoints",
            "company_rag": "Company-specific Q&A via /ask-company endpoint",
            "document_management": "Add company documents via /add-company-document endpoint",
            "company_listing": "List available companies via /companies endpoint"
        }
    }

if __name__ == "__main__":
    # Run the FastAPI application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8008,
        reload=True,  # Enable auto-reload during development
        log_level="info"
    )
