#!/usr/bin/env python3
"""
Test script for lead processing functionality.
Tests the flatten_lead_to_text function and lead processing pipeline.
"""

import json
from lead_processor import flatten_lead_to_text, process_leads_for_embedding, prepare_documents_for_vector_store, get_processing_summary

def test_flatten_lead_to_text():
    """Test the flatten_lead_to_text function with sample lead data."""
    
    # Sample lead data based on the structure from Firebase documentation
    sample_lead = {
        "id": "test_lead_001",
        "concernPerson": "John Smith",
        "projectCategory": "Industrial",
        "status": "New Lead",
        "generatedAt": "2025-01-15",
        "lastContactDate": "2025-01-20",
        "lastDiscussion": "Discussed project requirements and timeline",
        "nextSteps": "Schedule site visit and provide detailed quote",
        "projectStage": "Initial Enquiry",
        "createdById": "user123",
        "createdBy": "John Doe",
        "assignedToId": "agent456", 
        "assignedTo": "Jane Smith",
        "updatedAt": "2025-01-20T10:30:00Z",
        "clientDetails": {
            "name": "John Smith",
            "phoneNumber": "9876543210",
            "city": "Mumbai"
        }
    }
    
    print("=== Testing flatten_lead_to_text ===")
    print("Sample lead data:")
    print(json.dumps(sample_lead, indent=2))
    print("\nFlattened text:")
    
    flattened = flatten_lead_to_text(sample_lead, "Kalco")
    print(f"'{flattened}'")
    print(f"\nLength: {len(flattened)} characters")
    
    return flattened

def test_lead_processing_pipeline():
    """Test the complete lead processing pipeline."""
    
    # Sample leads data
    sample_leads = [
        {
            "id": "lead_001",
            "concernPerson": "Alice Johnson",
            "projectCategory": "Commercial",
            "status": "In Progress",
            "generatedAt": "2025-01-10",
            "lastContactDate": "2025-01-18",
            "projectStage": "Quotation Sent",
            "createdById": "user123",
            "createdBy": "John Doe",
            "assignedToId": "agent789",
            "assignedTo": "Mike Wilson",
            "updatedAt": "2025-01-18T14:20:00Z",
            "clientDetails": {
                "name": "Alice Johnson",
                "phoneNumber": "9111111111",
                "city": "Delhi"
            }
        },
        {
            "id": "lead_002",
            "concernPerson": "Bob Wilson",
            "projectCategory": "Residential",
            "status": "New Lead",
            "generatedAt": "2025-01-12",
            "createdById": "user456",
            "createdBy": "Sarah Connor",
            "assignedToId": "agent456",
            "assignedTo": "Jane Smith",
            "updatedAt": "2025-01-12T09:15:00Z",
            "clientDetails": {
                "name": "Bob Wilson",
                "phoneNumber": "9222222222",
                "city": "Bangalore"
            }
        },
        {
            "id": "lead_003",
            "concernPerson": "Carol Brown",
            "projectCategory": "Industrial",
            "status": "Follow-up Required",
            "generatedAt": "2025-01-08",
            "lastContactDate": "2025-01-15",
            "lastDiscussion": "Waiting for technical specifications",
            "nextSteps": "Follow up on specifications and prepare proposal",
            "createdById": "user123",
            "createdBy": "John Doe",
            "assignedToId": "agent789",
            "assignedTo": "Mike Wilson",
            "updatedAt": "2025-01-15T16:45:00Z",
            "clientDetails": {
                "name": "Carol Brown",
                "phoneNumber": "9333333333",
                "city": "Chennai"
            }
        }
    ]
    
    print("\n=== Testing Lead Processing Pipeline ===")
    print(f"Processing {len(sample_leads)} sample leads...")
    
    # Process leads for embedding
    grouped_leads = process_leads_for_embedding(sample_leads, "Kalco")
    
    print(f"\nGrouped leads by creator-assignee combination:")
    for grouping_key, leads in grouped_leads.items():
        print(f"  {grouping_key}: {len(leads)} leads")
    
    # Prepare documents for vector store
    documents = prepare_documents_for_vector_store(grouped_leads)
    
    print(f"\nTotal documents ready for embedding: {len(documents)}")
    
    # Get processing summary
    summary = get_processing_summary(grouped_leads)
    
    print(f"\nProcessing Summary:")
    print(json.dumps(summary, indent=2))
    
    print(f"\nSample processed document:")
    if documents:
        sample_doc = documents[0]
        print(json.dumps(sample_doc, indent=2))
    
    return grouped_leads, documents, summary

def test_edge_cases():
    """Test edge cases and error handling."""
    
    print("\n=== Testing Edge Cases ===")
    
    # Test with minimal lead data
    minimal_lead = {
        "id": "minimal_001"
    }
    
    print("Testing with minimal lead data:")
    flattened = flatten_lead_to_text(minimal_lead, "TestCompany")
    print(f"Result: '{flattened}'")
    
    # Test with empty/null values
    lead_with_nulls = {
        "id": "null_test_001",
        "concernPerson": "",
        "status": "N/A",
        "city": None,
        "generatedAt": "",
        "clientDetails": {
            "name": None,
            "phoneNumber": "",
            "city": "-"
        }
    }
    
    print("\nTesting with null/empty values:")
    flattened_nulls = flatten_lead_to_text(lead_with_nulls, "TestCompany")
    print(f"Result: '{flattened_nulls}'")

if __name__ == "__main__":
    """Run all tests."""
    print("Lead Processing Tests")
    print("=" * 50)
    
    # Test individual function
    test_flatten_lead_to_text()
    
    # Test complete pipeline
    test_lead_processing_pipeline()
    
    # Test edge cases
    test_edge_cases()
    
    print("\n" + "=" * 50)
    print("All tests completed!")
