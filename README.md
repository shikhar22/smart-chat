# AI Chat Agent

A basic AI agent built with LangChain that can answer basic questions. Now includes both CLI interface and REST API endpoints via FastAPI.

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

## Running the Applications

### CLI Agent (Original)
Run the command-line interface:
```bash
python agent.py
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

### Streamlit App
Run the Streamlit web interface:
```bash
streamlit run streamlit_app.py
```

## API Endpoints

### Health Check
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

### Models
- **GET** `/models` - List available OpenAI models

## Example API Usage

### Using curl:
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

# Ask a question
response = requests.post(
    "http://localhost:8008/ask",
    json={"question": "What is machine learning?"}
)
print(response.json())
```

### Using the provided client:
```bash
python client_example.py
```

## Features

- **CLI Interface**: Interactive command-line chat
- **REST API**: FastAPI-powered endpoints for integration
- **Web Interface**: Streamlit app for web-based interaction
- **Flexible Models**: Support for different OpenAI models
- **Temperature Control**: Adjustable response creativity
- **CORS Enabled**: Ready for web applications
- **Auto-documentation**: Built-in API docs at `/docs`

## Project Structure

- `agent.py` - Core AI agent class and CLI interface
- `main.py` - FastAPI REST API server
- `streamlit_app.py` - Streamlit web interface
- `client_example.py` - Example API client and usage
- `requirements.txt` - Python dependencies
- `setup.sh` - Setup script
- `.env` - Environment variables (create this file)

## Usage Examples

The agent can answer questions about various topics through multiple interfaces:

1. **CLI**: Direct terminal interaction
2. **API**: Programmatic access via REST endpoints
3. **Web**: Browser-based interface via Streamlit

Perfect for integrating AI chat capabilities into larger applications!
