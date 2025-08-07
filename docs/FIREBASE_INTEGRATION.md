# Firebase Integration Documentation

## Overview

This implementation provides a FastAPI POST endpoint `/update-data` that accepts company names and dynamically fetches lead data from separate Firebase projects for each company.

## Features

### 🚀 FastAPI Endpoint
- **Endpoint**: `POST /update-data`
- **Request Body**: `{"company": "CompanyName"}`
- **Response**: JSON with lead data and metadata
- **Error Handling**: Proper HTTP status codes and error messages

### 🔧 Firebase Client Utility
- **Dynamic Firebase Initialization**: Separate Firebase app per company
- **Configuration Management**: Service account keys stored per company
- **Data Fetching**: Retrieves leads collection from Firestore
- **Validation**: Checks Firebase configuration existence and validity

### 📋 Data Processing
- **Structured Response**: Pydantic models for request/response validation
- **Lead Processing**: Currently returns raw lead data (ready for downstream processing)
- **Metadata**: Includes lead count, company name, and processing status

## Implementation Details

### File Structure
```
/firebase_config/          # Firebase service account keys
├── README.md              # Setup instructions
├── Kalco.json            # Example configuration (placeholder values)
└── [Company].json        # Add more company configs here

firebase_client.py         # Firebase utility functions
main.py                   # FastAPI application (updated)
test_firebase_endpoint.py  # Test suite
requirements.txt          # Updated with firebase-admin
```

### Key Components

#### 1. Firebase Client Manager (`firebase_client.py`)
```python
class FirebaseClientManager:
    - _initialize_firebase_app()  # Dynamic app initialization
    - _get_firestore_client()     # Firestore client per company
    - fetch_leads()               # Fetch leads collection
    - validate_company_config()   # Configuration validation
```

#### 2. FastAPI Endpoint (`main.py`)
```python
@app.post("/update-data", response_model=UpdateDataResponse)
async def update_data(request: UpdateDataRequest):
    # Validates company configuration
    # Fetches leads using Firebase client
    # Returns structured response
```

#### 3. Pydantic Models
```python
class UpdateDataRequest:
    company: str

class UpdateDataResponse:
    status: str
    message: str
    company: str
    leads_count: int
    leads: List[Dict[str, Any]]
```

## Setup Instructions

### 1. Install Dependencies
```bash
pip install firebase-admin==6.5.0
```

### 2. Configure Firebase Projects
1. Create separate Firebase projects for each company
2. Generate service account keys for each project
3. Place JSON files in `firebase_config/` directory
4. Name files as `{CompanyName}.json`

### 3. Run the Server
```bash
python main.py
# Server runs on http://localhost:8008
```

## Usage Examples

### Test with cURL
```bash
# Valid company
curl -X POST "http://localhost:8008/update-data" \
     -H "Content-Type: application/json" \
     -d '{"company": "Kalco"}'

# Invalid company
curl -X POST "http://localhost:8008/update-data" \
     -H "Content-Type: application/json" \
     -d '{"company": "NonExistent"}'
```

### Test with Python
```python
import requests

response = requests.post(
    "http://localhost:8008/update-data",
    json={"company": "Kalco"}
)

data = response.json()
print(f"Fetched {data['leads_count']} leads")
```

### Run Test Suite
```bash
python test_firebase_endpoint.py
```

## API Response Examples

### Success Response
```json
{
  "status": "success",
  "message": "Successfully fetched 2012 leads for company 'Kalco'",
  "company": "Kalco",
  "leads_count": 2012,
  "leads": [
    {
      "id": "00dhsbntxUxlUueILNYl",
      "concernPerson": "Firoz Khan",
      "projectCategory": "Industrial",
      "status": "Order Drop",
      "clientDetails": {
        "name": "Firoz Khan",
        "phoneNumber": "9999704407",
        "city": "Greater Noida"
      },
      // ... more lead data
    }
  ]
}
```

### Error Response
```json
{
  "detail": "Firebase configuration not found for company 'NonExistent'. Please ensure firebase_config/NonExistent.json exists."
}
```

## Security Considerations

### 🔒 Service Account Keys
- **Never commit real keys to version control**
- Use `.gitignore` to exclude `firebase_config/*.json`
- Store keys securely in production environments
- Use environment-specific Firebase projects

### 🛡️ Access Control
- Consider implementing authentication for the endpoint
- Add rate limiting for production use
- Validate company names against allowed list
- Implement proper logging and monitoring

## Extending the Implementation

### 🔄 Downstream Processing
The current implementation stubs downstream processing. You can extend it by:

```python
@app.post("/update-data")
async def update_data(request: UpdateDataRequest):
    # ... existing code ...
    
    # Add downstream processing here:
    # 1. Data transformation
    processed_leads = transform_leads(leads)
    
    # 2. Store in database
    store_leads_in_db(company_name, processed_leads)
    
    # 3. Trigger workflows
    trigger_lead_processing_workflow(company_name, processed_leads)
    
    # 4. Send notifications
    notify_stakeholders(company_name, len(processed_leads))
    
    return UpdateDataResponse(...)
```

### 📊 Additional Endpoints
Consider adding:
- `GET /companies` - List available companies
- `GET /companies/{company}/status` - Check Firebase connection status
- `POST /companies/{company}/sync` - Force data synchronization
- `GET /companies/{company}/stats` - Get lead statistics

## Testing

### Automated Tests
The test suite (`test_firebase_endpoint.py`) covers:
- ✅ Valid company requests
- ✅ Invalid company error handling
- ✅ Firebase client utility functions
- ✅ Response format validation

### Manual Testing
1. **API Documentation**: Visit `http://localhost:8008/docs`
2. **Interactive Testing**: Use FastAPI's built-in interface
3. **cURL Commands**: Test from command line
4. **Postman Collection**: Create collection for team testing

## Monitoring and Logging

### Current Logging
- Firebase connection status
- Lead fetch operations
- Error conditions

### Production Recommendations
- Add structured logging (JSON format)
- Monitor Firebase usage and quotas
- Track endpoint performance metrics
- Set up alerts for failures

## Performance Considerations

### Current Implementation
- Connection pooling per company
- Efficient Firestore queries
- Response pagination (if needed)

### Optimization Opportunities
- Cache Firebase credentials
- Implement lead data caching
- Add async processing for large datasets
- Consider batch operations for multiple companies

## Troubleshooting

### Common Issues

1. **Firebase Connection Errors**
   - Check service account key validity
   - Verify Firebase project permissions
   - Ensure Firestore is enabled

2. **Import Errors**
   - Confirm firebase-admin installation
   - Check virtual environment activation

3. **Port Conflicts**
   - Use different port if 8008 is occupied
   - Check running processes with `lsof -i :8008`

4. **Permission Denied**
   - Verify service account has Firestore read permissions
   - Check Firebase project settings

## Next Steps

1. **Add Authentication**: Implement API key or OAuth
2. **Enhanced Validation**: Add company whitelist/blacklist
3. **Data Processing**: Implement actual downstream workflows
4. **Monitoring**: Add comprehensive logging and metrics
5. **Documentation**: Create OpenAPI specifications
6. **Testing**: Add integration and load tests
