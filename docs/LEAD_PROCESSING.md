# Lead Processing Implementation

## Overview

This implementation provides comprehensive lead processing functionality that fetches leads from Firebase, groups them by `createdById` and `assignedToId`, and prepares them for embedding in vector stores. The system transforms raw lead data into natural language documents suitable for AI/ML processing with enhanced metadata for better querying and analysis.

## Key Features

### 🔄 Lead Processing Pipeline
- **Fetch leads** from Firebase using existing infrastructure
- **Group leads** by both `createdById` and `assignedToId` for comprehensive organization
- **Flatten leads** into natural language text optimized for embeddings
- **Prepare documents** with enhanced metadata including creator and assignee information
- **Generate processing summaries** with detailed statistics on creators, assignees, and groupings

### 📝 Natural Language Processing
- Converts structured lead data into readable paragraphs
- Prioritizes important fields: Enquiry Date, City, Project Stage, Client Name, etc.
- Includes creator and assignee information in natural language
- Handles missing/null/empty values gracefully
- Formats dates in human-readable format
- Avoids JSON or bullet formatting for natural text flow

### 🏗️ Document Structure
Each processed document has:
```json
{
  "id": "lead_12345",
  "text": "Lead from Kalco. Enquiry Date: January 15, 2025...",
  "metadata": {
    "company": "Kalco",
    "leadId": "lead_12345", 
    "createdById": "user123",
    "createdBy": "John Doe",
    "assignedToId": "agent456",
    "assignedTo": "Jane Smith",
    "city": "Mumbai",
    "updatedAt": "2025-01-20T10:30:00Z",
    "groupingKey": "created:user123|assigned:agent456"
  }
}
```

## Implementation Files

### 1. `lead_processor.py`
Core processing functions:
- `flatten_lead_to_text(lead: dict, company: str) -> str`
- `process_leads_for_embedding(leads: List[Dict], company: str) -> Dict`
- `prepare_documents_for_vector_store(grouped_leads: Dict) -> List[Dict]`
- `get_processing_summary(grouped_leads: Dict) -> Dict`

### 2. Enhanced `main.py`
Updated API endpoints:
- **Enhanced `/update-data`**: Now includes processed documents alongside raw leads
- **New `/process-leads`**: Returns only processed documents ready for embedding

### 3. Test and Example Files
- `test_lead_processing.py`: Comprehensive test suite
- `example_lead_processing.py`: Usage examples and API documentation

## API Endpoints

### POST `/update-data`
Enhanced endpoint that returns both raw leads and processed documents.

**Request:**
```json
{
  "company": "Kalco"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Successfully fetched and processed 2012 leads...",
  "company": "Kalco",
  "leads_count": 2012,
  "leads": [...],  // Raw Firebase data
  "processed_leads": {
    "user123": [...],  // Grouped by createdById
    "user456": [...]
  },
  "documents_ready_for_embedding": [...],  // Flattened list
  "processing_summary": {
    "total_leads_processed": 2012,
    "total_creators": 5,
    "leads_by_creator": {...},
    "creators_list": [...]
  }
}
```

### POST `/process-leads`
New endpoint that returns only processed documents (lighter response).

**Request:**
```json
{
  "company": "Kalco"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Successfully processed 2012 leads...",
  "company": "Kalco", 
  "total_leads": 2012,
  "documents_ready_for_embedding": [...],
  "processing_summary": {...}
}
```

## Text Flattening Logic

The `flatten_lead_to_text()` function:

1. **Starts with company context**: "Lead from {company}"
2. **Prioritizes key fields** in order of importance:
   - Enquiry Date
   - City  
   - Project Stage
   - Client Name
   - Last Contact Date
   - Last Discussion
   - Next Steps
3. **Handles nested data** (e.g., `clientDetails.city`)
4. **Formats dates** into readable format (e.g., "January 15, 2025")
5. **Skips empty values**: null, "", "N/A", "TBD", etc.
6. **Creates natural paragraphs**: No JSON or bullet formatting
7. **Includes additional fields** if space permits

### Example Output
```
Lead from Kalco. Enquiry Date: January 15, 2025. City: Mumbai. Project Stage: Initial Enquiry. Client Name: John Smith. Last Contact Date: January 20, 2025. Last Discussion: Discussed project requirements and timeline. Next Steps: Schedule site visit and provide detailed quote. Contact Person: John Smith. Status: New Lead. Project Category: Industrial.
```

## Grouping by createdById and assignedToId

Leads are organized by both creator and assignee for comprehensive analysis:

```json
{
  "created:user123|assigned:agent456": [
    {"id": "lead_001", "text": "...", "metadata": {...}},
    {"id": "lead_002", "text": "...", "metadata": {...}}
  ],
  "created:user456|assigned:agent789": [
    {"id": "lead_003", "text": "...", "metadata": {...}}
  ]
}
```

Processing summary provides detailed insights:
- Total leads per creator (`leads_by_creator`)
- Total leads per assignee (`leads_by_assignee`)
- Combined groupings (`leads_by_group`)
- Most active creators and assignees
- Distribution analysis across the organization

## Integration with Vector Stores

The processed documents are ready for embedding:

1. **Use `text` field** for embedding generation
2. **Use `id` as document identifier** in vector store
3. **Store `metadata`** for filtering and retrieval
4. **Filter by**:
   - Company (`metadata.company`)
   - Creator (`metadata.createdById` or `metadata.createdBy`) 
   - Assignee (`metadata.assignedToId` or `metadata.assignedTo`)
   - Location (`metadata.city`)
   - Recency (`metadata.updatedAt`)
   - Combined grouping (`metadata.groupingKey`)

## Testing

Run the test suite:
```bash
python3 test_lead_processing.py
```

Test with live API (when server running):
```bash
# Test enhanced endpoint
curl -X POST http://localhost:8008/update-data \
     -H 'Content-Type: application/json' \
     -d '{"company": "Kalco"}'

# Test new endpoint  
curl -X POST http://localhost:8008/process-leads \
     -H 'Content-Type: application/json' \
     -d '{"company": "Kalco"}'
```

## Error Handling

The implementation includes robust error handling:
- **Firebase connection errors**
- **Missing company configurations**
- **Invalid lead data structures**
- **Processing exceptions**
- **Graceful degradation** for missing fields

## Performance Considerations

- **Efficient grouping** using dictionary lookups
- **Minimal memory footprint** with generator patterns where applicable
- **Configurable text length** to prevent overly long documents
- **Lazy evaluation** of additional fields to control processing time

## Future Enhancements

Potential improvements:
1. **Caching** processed documents
2. **Incremental processing** for updated leads only
3. **Batch processing** for large datasets
4. **Custom field prioritization** per company
5. **Multi-language support** for international leads
6. **Advanced text preprocessing** (stemming, entity extraction)

## Dependencies

The implementation uses only standard library modules plus existing project dependencies:
- `typing` - Type hints
- `datetime` - Date formatting
- `logging` - Error tracking
- `json` - Data serialization
- Existing Firebase and FastAPI infrastructure
