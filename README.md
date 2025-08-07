# AI Chat Agent with RAG

A comprehensive AI agent built with LangChain that supports both general Q&A and company-specific knowledge retrieval using RAG (Retrieval Augmented Generation). Features include CLI interface, REST API endpoints via FastAPI, and company document management.

## Features

- **General AI Chat**: Basic question-answering using OpenAI models
- **Company-Specific RAG**: Ask questions about specific companies using their knowledge base
- **Multi-format Document Support**: PDF, DOCX, TXT, and JSON document ingestion
- **Vector Search**: ChromaDB-powered semantic search
- **REST API**: FastAPI-based API with comprehensive endpoints
- **Interactive Testing**: Built-in test client and sample data

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On macOS/Linux
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file and add your OpenAI API key:
```
OPENAI_API_KEY=your_openai_api_key_here
```

4. Set up sample company data (optional):
```bash
python setup_companies.py
```

## Running the Applications

### CLI Agent (Original)
Run the command-line interface:
```bash
python agent.py
```

### RAG Agent CLI
Test the RAG functionality directly:
```bash
python rag_agent.py
```

### FastAPI Server
Start the REST API server:
```bash
python main.py
```

The API will be available at:
- **Server**: http://localhost:8008
- **Interactive Docs**: http://localhost:8008/docs
- **Alternative Docs**: http://localhost:8008/redoc

### Test the RAG API
Run the interactive test client:
```bash
python test_rag_client.py
```

### Streamlit App
Run the Streamlit web interface:
```bash
streamlit run streamlit_app.py
```

## API Endpoints

### General Chat Endpoints
- **GET** `/health` - Check if the API is running
- **GET** `/` - Root endpoint with basic info

### AI Chat
- **POST** `/ask` - Ask a question (detailed response)
  ```json
  {
    "question": "What is artificial intelligence?",
    "model_name": "gpt-3.5-turbo",
    "temperature": 0.7
  }
  ```

- **POST** `/chat` - Simple chat endpoint
  ```json
  {
    "question": "Explain machine learning",
    "model_name": "gpt-3.5-turbo",
    "temperature": 0.7
  }
  ```

### Company-Specific RAG Endpoints

- **POST** `/ask-company` - Ask questions about a specific company
  ```json
  {
    "question": "What does the company do?",
    "company_name": "TechCorp",
    "model_name": "gpt-3.5-turbo",
    "temperature": 0.7
  }
  ```

- **GET** `/companies` - List all available companies
  ```json
  {
    "companies": ["TechCorp", "GreenEnergy", "FinanceFirst"],
    "count": 3
  }
  ```

- **POST** `/add-company-document` - Add a document for a company
  ```json
  {
    "company_name": "MyCompany",
    "content": "Company information and policies...",
    "filename": "company_overview.txt"
  }
  ```

- **POST** `/create-company-vectorstore/{company_name}` - Create/recreate vector store
  ```bash
  curl -X POST "http://localhost:8008/create-company-vectorstore/TechCorp?force_recreate=true"
  ```

### Models
- **GET** `/models` - List available OpenAI models and API features

## Example API Usage

### Company-Specific Questions:
```bash
# Ask about a company
curl -X POST "http://localhost:8008/ask-company" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the vacation policy?",
    "company_name": "TechCorp"
  }'

# List available companies
curl http://localhost:8008/companies

# Add a company document
curl -X POST "http://localhost:8008/add-company-document" \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "NewCorp",
    "content": "NewCorp is a startup...",
    "filename": "overview.txt"
  }'
```

### General AI Questions:
```bash
# Health check
curl http://localhost:8008/health

# Ask a question
curl -X POST "http://localhost:8008/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Python?"}'

# Simple chat
curl -X POST "http://localhost:8008/chat" \
  -H "Content-Type: application/json" \
  -d '{"question": "Tell me about AI"}'
```

### Using Python:
```python
import requests

# Ask a company-specific question
response = requests.post(
    "http://localhost:8008/ask-company",
    json={
        "question": "What does the company do?",
        "company_name": "TechCorp"
    }
)
print(response.json())

# Ask a general question
response = requests.post(
    "http://localhost:8008/ask",
    json={"question": "What is machine learning?"}
)
print(response.json())
```

### Using the provided test client:
```bash
python test_rag_client.py
```

## Company Document Management

### Supported File Formats
- **Text files** (.txt)
- **PDF documents** (.pdf)
- **Word documents** (.docx, .doc)
- **JSON files** (.json)

### Adding Company Documents

1. **Via API**:
   ```python
   import requests
   
   requests.post("http://localhost:8008/add-company-document", json={
       "company_name": "MyCompany",
       "content": "Company information...",
       "filename": "info.txt"
   })
   ```

2. **Via file system**:
   - Create directory: `companies/MyCompany/`
   - Add documents to the directory
   - Run: `POST /create-company-vectorstore/MyCompany`

### Sample Questions You Can Ask

With the provided sample companies, try these questions:

- **TechCorp**: "What does TechCorp do?", "What is the remote work policy?", "How much is the training budget?"
- **GreenEnergy**: "What services does GreenEnergy offer?", "What is the carbon neutral goal?", "What safety training is required?"
- **FinanceFirst**: "What banking services are available?", "What are the branch hours?", "What is the retirement plan?"

## Features

- **CLI Interface**: Interactive command-line chat
- **REST API**: FastAPI-powered endpoints for integration
- **RAG System**: Company-specific knowledge retrieval
- **Vector Search**: ChromaDB-powered semantic search
- **Multi-format Support**: PDF, DOCX, TXT, JSON document ingestion
- **Web Interface**: Streamlit app for web-based interaction
- **Flexible Models**: Support for different OpenAI models
- **Temperature Control**: Adjustable response creativity
- **CORS Enabled**: Ready for web applications
- **Auto-documentation**: Built-in API docs at `/docs`

## Project Structure

- `agent.py` - Core AI agent class and CLI interface
- `rag_agent.py` - RAG agent for company-specific Q&A
- `main.py` - FastAPI REST API server with RAG endpoints
- `streamlit_app.py` - Streamlit web interface
- `setup_companies.py` - Script to set up sample company data
- `test_rag_client.py` - Interactive test client for RAG functionality
- `requirements.txt` - Python dependencies (updated with RAG packages)
- `setup.sh` - Setup script
- `.env` - Environment variables (create this file)
- `companies/` - Directory for company documents (auto-created)
- `vectordb/` - Directory for vector databases (auto-created)

## Quick Start Guide

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up your OpenAI API key**:
   ```bash
   echo "OPENAI_API_KEY=your_key_here" > .env
   ```

3. **Set up sample companies**:
   ```bash
   python setup_companies.py
   ```

4. **Start the API server**:
   ```bash
   python main.py
   ```

5. **Test the RAG functionality**:
   ```bash
   python test_rag_client.py
   ```

## Usage Examples

The agent can answer both general questions and company-specific questions through multiple interfaces:

1. **CLI**: Direct terminal interaction for testing
2. **API**: Programmatic access via REST endpoints
3. **Web**: Browser-based interface via Streamlit
4. **RAG**: Company-specific knowledge retrieval

Perfect for building AI assistants that need access to company-specific information and policies!
