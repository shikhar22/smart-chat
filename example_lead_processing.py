#!/usr/bin/env python3
"""
Example usage of the lead processing functionality.
Shows how to fetch and process leads for embedding.
"""

import json
from typing import Dict, Any

# Note: requests import is optional for the demo
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    print("Note: 'requests' module not available. Showing structure examples only.")

def test_update_data_endpoint(base_url: str = "http://localhost:8008", company: str = "Kalco"):
    """Test the enhanced /update-data endpoint."""
    
    if not HAS_REQUESTS:
        print("requests module not available. Install with: pip install requests")
        return
    
    print(f"=== Testing Enhanced /update-data Endpoint ===")
    print(f"Company: {company}")
    print(f"Base URL: {base_url}")
    
    try:
        response = requests.post(
            f"{base_url}/update-data",
            json={"company": company},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"✅ Success!")
            print(f"Status: {data['status']}")
            print(f"Message: {data['message']}")
            print(f"Total leads fetched: {data['leads_count']}")
            
            if 'processing_summary' in data and data['processing_summary']:
                summary = data['processing_summary']
                print(f"\n📊 Processing Summary:")
                print(f"  - Total leads processed: {summary['total_leads_processed']}")
                print(f"  - Total groups: {summary['total_groups']}")
                print(f"  - Unique creators: {summary['total_unique_creators']}")
                print(f"  - Unique assignees: {summary['total_unique_assignees']}")
                print(f"  - Creators: {summary['creators_list']}")
                print(f"  - Assignees: {summary['assignees_list']}")
                print(f"  - Leads by creator:")
                for creator, count in summary['leads_by_creator'].items():
                    print(f"    • {creator}: {count} leads")
                print(f"  - Leads by assignee:")
                for assignee, count in summary['leads_by_assignee'].items():
                    print(f"    • {assignee}: {count} leads")
            
            if 'documents_ready_for_embedding' in data and data['documents_ready_for_embedding']:
                docs = data['documents_ready_for_embedding']
                print(f"\n📝 Documents ready for embedding: {len(docs)}")
                
                # Show a sample document
                if docs:
                    print(f"\nSample document:")
                    sample_doc = docs[0]
                    print(f"  ID: {sample_doc['id']}")
                    print(f"  Text preview: {sample_doc['text'][:100]}...")
                    print(f"  Metadata: {json.dumps(sample_doc['metadata'], indent=4)}")
            
        else:
            print(f"❌ Request failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error: {error_data.get('detail', 'Unknown error')}")
            except:
                print(f"Error: {response.text}")
                
    except requests.RequestException as e:
        print(f"❌ Request failed: {str(e)}")

def test_process_leads_endpoint(base_url: str = "http://localhost:8008", company: str = "Kalco"):
    """Test the new /process-leads endpoint."""
    
    if not HAS_REQUESTS:
        print("requests module not available. Install with: pip install requests")
        return
    
    print(f"\n=== Testing /process-leads Endpoint ===")
    print(f"Company: {company}")
    print(f"Base URL: {base_url}")
    
    try:
        response = requests.post(
            f"{base_url}/process-leads",
            json={"company": company},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"✅ Success!")
            print(f"Status: {data['status']}")
            print(f"Message: {data['message']}")
            print(f"Total leads: {data['total_leads']}")
            
            summary = data['processing_summary']
            print(f"\n📊 Processing Summary:")
            print(f"  - Total leads processed: {summary['total_leads_processed']}")
            print(f"  - Total groups: {summary['total_groups']}")
            print(f"  - Unique creators: {summary['total_unique_creators']}")
            print(f"  - Unique assignees: {summary['total_unique_assignees']}")
            print(f"  - Leads by creator: {summary['leads_by_creator']}")
            print(f"  - Leads by assignee: {summary['leads_by_assignee']}")
            
            docs = data['documents_ready_for_embedding']
            print(f"\n📝 Documents ready for embedding: {len(docs)}")
            
            # Show sample documents from different groups
            groups_shown = set()
            for doc in docs[:3]:  # Show up to 3 samples
                grouping_key = doc['metadata']['groupingKey']
                if grouping_key not in groups_shown:
                    print(f"\n--- Sample document from group '{grouping_key}' ---")
                    print(f"ID: {doc['id']}")
                    print(f"City: {doc['metadata']['city']}")
                    print(f"Created By: {doc['metadata']['createdBy']} (ID: {doc['metadata']['createdById']})")
                    print(f"Assigned To: {doc['metadata']['assignedTo']} (ID: {doc['metadata']['assignedToId']})")
                    print(f"Text: {doc['text']}")
                    groups_shown.add(grouping_key)
            
        else:
            print(f"❌ Request failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error: {error_data.get('detail', 'Unknown error')}")
            except:
                print(f"Error: {response.text}")
                
    except requests.RequestException as e:
        print(f"❌ Request failed: {str(e)}")

def demonstrate_document_structure():
    """Show the structure of documents ready for embedding."""
    
    print(f"\n=== Document Structure for Vector Store ===")
    
    sample_document = {
        "id": "lead_12345",
        "text": "Lead from Kalco. Enquiry Date: January 15, 2025. City: Mumbai. Project Stage: Initial Enquiry. Client Name: John Smith. Last Contact Date: January 20, 2025. Last Discussion: Discussed project requirements and timeline. Next Steps: Schedule site visit and provide detailed quote. Assigned To: Jane Smith. Created By: John Doe.",
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
    
    print("Each document has this structure:")
    print(json.dumps(sample_document, indent=2))
    
    print(f"Key points:")
    print(f"• 'id': Unique identifier for the document")
    print(f"• 'text': Natural language paragraph suitable for embedding")
    print(f"• 'metadata': Structured data for filtering and organization")
    print(f"  - 'company': Company name")
    print(f"  - 'leadId': Original lead ID from Firebase")
    print(f"  - 'createdById' & 'createdBy': Creator ID and name")
    print(f"  - 'assignedToId' & 'assignedTo': Assignee ID and name")
    print(f"  - 'city': Geographic information")
    print(f"  - 'updatedAt': Timestamp for freshness tracking")
    print(f"  - 'groupingKey': Combined creator-assignee grouping key")

def show_usage_examples():
    """Show examples of how to use the processed data."""
    
    print(f"\n=== Usage Examples ===")
    
    print(f"1. Vector Store Integration:")
    print(f"   For each document in 'documents_ready_for_embedding':")
    print(f"   - Use 'text' field for embedding generation")
    print(f"   - Use 'id' as document identifier")
    print(f"   - Store 'metadata' for filtering and retrieval")
    
    print(f"2. Grouping by Creator and Assignee:")
    print(f"   Access the 'processing_summary' to see:")
    print(f"   - How many leads each creator has ('leads_by_creator')")
    print(f"   - How many leads each assignee has ('leads_by_assignee')")
    print(f"   - Combined creator-assignee groups ('leads_by_group')")
    print(f"   - Which creators and assignees are most active")
    
    print(f"\n3. Geographic Analysis:")
    print(f"   Filter documents by 'metadata.city' to:")
    print(f"   - Analyze regional lead patterns")
    print(f"   - Route leads to local teams")
    
    print(f"\n4. Assignment Analysis:")
    print(f"   Filter documents by 'metadata.assignedToId' or 'assignedTo' to:")
    print(f"   - Track individual agent performance")
    print(f"   - Analyze workload distribution")
    print(f"   - Identify unassigned leads")
    
    print(f"\n5. Creator Analysis:")
    print(f"   Filter documents by 'metadata.createdById' or 'createdBy' to:")
    print(f"   - Track lead generation sources")
    print(f"   - Analyze lead quality by creator")
    
    print(f"\n6. Time-based Processing:")
    print(f"   Use 'metadata.updatedAt' to:")
    print(f"   - Process only recent leads")
    print(f"   - Track lead lifecycle")

if __name__ == "__main__":
    """Run the example."""
    
    print("Lead Processing API Example")
    print("=" * 50)
    
    # Note: These will only work if the server is running and has Firebase configured
    print("Note: Server must be running at http://localhost:8008 with Firebase configured")
    print("Run these tests manually when server is available:")
    print()
    
    # Show document structure
    demonstrate_document_structure()
    
    # Show usage examples
    show_usage_examples()
    
    print(f"\n=== API Test Commands ===")
    print(f"To test the API when server is running:")
    print(f"")
    print(f"# Test enhanced update-data endpoint")
    print(f"curl -X POST http://localhost:8008/update-data \\")
    print(f"     -H 'Content-Type: application/json' \\")
    print(f"     -d '{{\"company\": \"Kalco\"}}'")
    print(f"")
    print(f"# Test new process-leads endpoint")
    print(f"curl -X POST http://localhost:8008/process-leads \\")
    print(f"     -H 'Content-Type: application/json' \\")
    print(f"     -d '{{\"company\": \"Kalco\"}}'")
    
    print("\n" + "=" * 50)
    print("Example completed!")
    
    # Uncomment these lines to test with a running server:
    # test_update_data_endpoint()
    # test_process_leads_endpoint()
