#!/usr/bin/env python3
"""
FastAPI application for AI Chat Agent
Provides REST API endpoints to interact with the AI agent.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import uvicorn
from agent import BasicAIAgent

# Pydantic models for request/response
class QuestionRequest(BaseModel):
    """Request model for asking a question."""
    question: str = Field(..., min_length=1, description="The question to ask the AI agent")
    model_name: Optional[str] = Field("gpt-3.5-turbo", description="OpenAI model to use")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=1.0, description="Temperature for response randomness")

class QuestionResponse(BaseModel):
    """Response model for question answers."""
    question: str
    answer: str
    model_used: str
    temperature: float

class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    message: str

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

# Global agent instance (will be initialized on first use)
agent_instance = None

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

@app.get("/models")
async def list_available_models():
    """
    List available OpenAI models that can be used.
    
    Returns:
        List of available model names
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
        "note": "Model availability depends on your OpenAI API access level"
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
