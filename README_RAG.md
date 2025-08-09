# Semantic RAG Pipeline API

A FastAPI application that implements a semantic RAG (Retrieval Augmented Generation) pipeline for processing and querying lead data using OpenAI Vector Store and GPT-4o.

## Features

- **Two Core Endpoints**:
  - `POST /update-leads` - Fetch leads from Firebase, embed, and store in OpenAI Vector Store
  - `POST /ask` - Semantic search and AI-powered question answering about leads

- **Technology Stack**:
  - FastAPI for REST API
  - OpenAI Vector Store for embeddings storage
  - OpenAI GPT-4o for question answering
  - Firebase Firestore for lead data storage
  - text-embedding-3-small for embeddings

## Quick Start

### 1. Environment Setup

```bash
# Clone/navigate to the project directory
cd ai-chat

# Run the setup script
./setup_rag.sh

# Set your OpenAI API key
export OPENAI_API_KEY='your-openai-api-key-here'
```

### 2. Firebase Configuration

Add Firebase service account JSON files to the `firebase_config/` directory:

```
firebase_config/
├── Kalco.json
├── TechCorp.json
├── FinanceFirst.json
└── GreenEnergy.json
```

### 3. Start the API Server

```bash
source .venv/bin/activate
python3 main.py
```

The API will be available at `http://localhost:8000` with documentation at `http://localhost:8000/docs`.

## API Endpoints

### POST /update-leads

Fetches leads from company-specific Firebase, flattens them to text, embeds using OpenAI, and upserts to vector store.

**Request:**
```json
{
  "companyName": "Kalco",
  "assignedTo": "Sales Manager",
  "assignedToId": "SM001",
  "forceRefresh": false
}
```

**Response:**
```json
{
  "companyName": "Kalco",
  "totalLeadsFetched": 150,
  "totalUpserted": 25,
  "totalSkipped": 125
}
```

### POST /ask

Performs semantic search on the company's lead data and answers questions using GPT-4o.

**Request:**
```json
{
  "companyName": "Kalco",
  "question": "How many leads do we have from Mumbai in the planning stage?"
}
```

**Response:**
```json
{
  "answer": "Based on the lead data, you have 12 leads from Mumbai that are currently in the planning stage...",
  "sources": [
    {
      "id": "LEAD123",
      "score": 0.95,
      "metadata": {
        "companyName": "Kalco",
        "projectCity": "Mumbai",
        "projectStage": "Planning"
      },
      "snippet": "Lead from Kalco: id=LEAD123. Project: Office Complex..."
    }
  ]
}
```

## Module Overview

### firebase_utils.py
- `init_firebase_app(companyName)` - Initialize Firebase app for a company
- `fetch_all_leads(companyName)` - Fetch all leads from Firebase

### flatten_utils.py
- `flattenLeadToText(lead, companyName)` - Convert lead data to readable text for embedding

### vectorstore_utils.py
- `getVectorStoreName(companyName)` - Generate vector store name
- `embed_texts(texts, batchSize)` - Create embeddings using text-embedding-3-small
- `upsert_lead_documents(companyName, items)` - Upload documents to OpenAI Vector Store
- `search_vector_store(companyName, query, topK)` - Semantic search in vector store

### main.py
- FastAPI application with the two core endpoints
- Request/response models and error handling

## Data Processing Flow

1. **Lead Fetching**: Fetch leads from company-specific Firebase collection
2. **Filtering**: Apply optional filters by assignedTo/assignedToId
3. **Change Detection**: Check existing metadata to determine which leads need updating
4. **Text Flattening**: Convert lead objects to readable text summaries
5. **Embedding**: Create vector embeddings using OpenAI's text-embedding-3-small
6. **Storage**: Upload to OpenAI Vector Store with metadata
7. **Search**: Semantic search when questions are asked
8. **Answer Generation**: Use GPT-4o with retrieved context to answer questions

## Lead Text Format

Leads are flattened to natural language text like:

```
Lead from Kalco: id=LEAD123. Enquiry Date: January 15, 2024. Project: New Office Building. City: Mumbai. Stage: Planning. Category: Commercial. Source: Website. Client: John Doe Construction. Phone: +91-9876543210. Follow-up summary: last contacted January 20, 2024, discussed: project timeline and budget, next follow-up scheduled for January 25, 2024. Updated: January 21, 2024.
```

## Metadata Schema

All metadata uses camelCase:

```json
{
  "companyName": "Kalco",
  "assignedTo": "Sales Manager",
  "assignedToId": "SM001", 
  "id": "LEAD123",
  "updatedAt": "2024-01-21T10:30:00Z",
  "projectCity": "Mumbai",
  "projectCategory": "Commercial",
  "generatedAt": "2024-01-15",
  "projectStage": "Planning",
  "projectSource": "Website"
}
```

## Example Usage

```python
import requests

# Update leads for a company
response = requests.post("http://localhost:8000/update-leads", json={
    "companyName": "Kalco",
    "forceRefresh": True
})
print(response.json())

# Ask a question
response = requests.post("http://localhost:8000/ask", json={
    "companyName": "Kalco", 
    "question": "What are our recent project enquiries from Mumbai?"
})
print(response.json()["answer"])
```

Run the example script:
```bash
python3 example_usage.py
```

## Testing

Run unit tests:
```bash
python3 test_rag_pipeline.py
```

The tests cover:
- Lead text flattening functionality
- Vector store name generation
- Integration test stubs with mocked dependencies

## Configuration

### Environment Variables
- `OPENAI_API_KEY` - Required for OpenAI API access

### Firebase Setup
- Place service account JSON files in `firebase_config/` directory
- Files should be named `{CompanyName}.json`
- Each company needs its own Firebase project

## Error Handling

- Robust logging throughout the pipeline
- Exponential backoff for API calls
- Graceful handling of missing data
- Detailed error messages in API responses

## Performance Considerations

- Batch processing for embeddings (default: 64 texts per batch)
- Batch processing for vector store uploads (default: 20 items per batch)
- Incremental updates based on `updatedAt` timestamps
- Connection pooling and retry logic

## Security Notes

- Firebase service account keys should be kept secure
- Never commit actual service account keys to version control
- Use environment-specific Firebase projects
- API key should be stored securely

## Dependencies

Key packages:
- `fastapi` - Web framework
- `openai` - OpenAI API client
- `firebase-admin` - Firebase SDK
- `backoff` - Retry logic
- `pydantic` - Data validation

See `requirements.txt` for complete list.

## Troubleshooting

### Common Issues

1. **OpenAI API Key Error**
   ```
   export OPENAI_API_KEY='your-key-here'
   ```

2. **Firebase Configuration Missing**
   - Add service account JSON files to `firebase_config/`
   - Ensure files are named correctly (`CompanyName.json`)

3. **Vector Store Upload Timeouts**
   - Check internet connection
   - Reduce batch sizes if needed
   - Monitor OpenAI API usage limits

4. **No Search Results**
   - Ensure `/update-leads` has been called first
   - Check that vector store was created successfully
   - Verify company name matches exactly

### Logs

The application provides detailed logging. Check logs for:
- Firebase connection status
- Embedding progress
- Vector store operations
- Search results

## Development

To extend the system:

1. **Add New Data Sources**: Implement new fetch functions in firebase_utils.py
2. **Modify Text Format**: Update flattenLeadToText in flatten_utils.py  
3. **Add Endpoints**: Extend main.py with new API endpoints
4. **Custom Embeddings**: Modify embed_texts in vectorstore_utils.py

## License

This project is for internal use and follows the company's software development guidelines.
