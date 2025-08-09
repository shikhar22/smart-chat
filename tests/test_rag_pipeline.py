#!/usr/bin/env python3
"""
Unit tests for the semantic RAG pipeline modules.
"""

import unittest
import os
from datetime import datetime

# Set a test API key to avoid initialization errors
os.environ["OPENAI_API_KEY"] = "test-key-for-testing"

from flatten_utils import flattenLeadToText
from vectorstore_utils import getVectorStoreName

class TestFlattenUtils(unittest.TestCase):
    """Test cases for flatten_utils module."""
    
    def test_flattenLeadToText_basic(self):
        """Test basic lead flattening functionality."""
        # Sample lead data
        lead = {
            "id": "LEAD123",
            "generatedAt": "2024-01-15",
            "projectName": "New Office Building",
            "projectCity": "Mumbai",
            "projectStage": "Planning",
            "projectCategory": "Commercial",
            "projectSource": "Website",
            "clientDetails": {
                "name": "John Doe Construction",
                "phoneNumber": "+91-9876543210"
            },
            "lastContactDate": "2024-01-20",
            "lastDiscussion": "Discussed project timeline and budget",
            "nextFollowUpDate": "2024-01-25",
            "updatedAt": "2024-01-21T10:30:00Z",
            "assignedTo": "Sales Manager",
            "assignedToId": "SM001"
        }
        
        company_name = "TestCompany"
        result = flattenLeadToText(lead, company_name)
        
        # Verify the result contains expected elements
        self.assertIn(f"Lead from {company_name}", result)
        self.assertIn("id=LEAD123", result)
        self.assertIn("Project: New Office Building", result)
        self.assertIn("City: Mumbai", result)
        self.assertIn("Client: John Doe Construction", result)
        self.assertIn("Phone: +91-9876543210", result)
        
    def test_flattenLeadToText_missing_fields(self):
        """Test flattening with missing or empty fields."""
        lead = {
            "id": "LEAD456",
            "projectName": "Small Renovation",
            "clientDetails": {
                "name": "Jane Smith",
                "phoneNumber": ""  # Empty phone
            },
            "projectCity": None,  # Null city
            "lastDiscussion": "--select--",  # Placeholder value
            "updatedAt": "2024-01-21"
        }
        
        company_name = "TestCompany"
        result = flattenLeadToText(lead, company_name)
        
        # Should contain basic info
        self.assertIn("Lead from TestCompany", result)
        self.assertIn("id=LEAD456", result)
        self.assertIn("Project: Small Renovation", result)
        self.assertIn("Client: Jane Smith", result)
        
        # Should not contain empty/placeholder values
        self.assertNotIn("Phone:", result)
        self.assertNotIn("City:", result)
        self.assertNotIn("--select--", result)
        
    def test_flattenLeadToText_nested_client_details(self):
        """Test extraction of nested client details."""
        lead = {
            "id": "LEAD789",
            "clientDetails": {
                "name": "ABC Corporation",
                "phoneNumber": "+91-1234567890",
                "email": "contact@abc.com"  # Email not in our extraction list
            },
            "projectCategory": "Residential"
        }
        
        company_name = "TestCompany"
        result = flattenLeadToText(lead, company_name)
        
        self.assertIn("Client: ABC Corporation", result)
        self.assertIn("Phone: +91-1234567890", result)
        self.assertIn("Category: Residential", result)
        # Email should not be included as it's not in our fields list
        self.assertNotIn("contact@abc.com", result)

class TestVectorStoreUtils(unittest.TestCase):
    """Test cases for vectorstore_utils module."""
    
    def test_getVectorStoreName(self):
        """Test vector store name generation."""
        self.assertEqual(getVectorStoreName("TechCorp"), "techcorp_leads")
        self.assertEqual(getVectorStoreName("Finance-First"), "finance-first_leads")
        self.assertEqual(getVectorStoreName("KALCO"), "kalco_leads")

class TestIntegration(unittest.TestCase):
    """Integration test stubs with mocked dependencies."""
    
    def setUp(self):
        """Set up test dependencies."""
        self.sample_leads = [
            {
                "id": "LEAD001",
                "projectName": "Office Complex",
                "clientDetails": {"name": "Client A", "phoneNumber": "+91-1111111111"},
                "assignedTo": "Manager A",
                "assignedToId": "MGA001",
                "updatedAt": "2024-01-15T10:00:00Z"
            },
            {
                "id": "LEAD002", 
                "projectName": "Residential Tower",
                "clientDetails": {"name": "Client B", "phoneNumber": "+91-2222222222"},
                "assignedTo": "Manager B",
                "assignedToId": "MGB001",
                "updatedAt": "2024-01-16T11:00:00Z"
            }
        ]
    
    def test_end_to_end_lead_processing_mock(self):
        """Test end-to-end lead processing with mocked vector store operations."""
        # This would be a full integration test with mocked OpenAI and Firebase calls
        
        company_name = "TestCompany"
        
        # Step 1: Mock fetch leads (would come from Firebase)
        leads = self.sample_leads
        
        # Step 2: Flatten leads to text
        flattened_texts = []
        for lead in leads:
            text = flattenLeadToText(lead, company_name)
            flattened_texts.append(text)
        
        # Verify flattening worked
        self.assertEqual(len(flattened_texts), 2)
        self.assertIn("Office Complex", flattened_texts[0])
        self.assertIn("Residential Tower", flattened_texts[1])
        
        # Step 3: Mock vector store operations
        # In a real test, you'd mock the OpenAI API calls
        mock_upsert_result = {
            "upserted": 2,
            "vector_store_id": "vs_mock_123",
            "message": "Mock upsert successful"
        }
        
        self.assertEqual(mock_upsert_result["upserted"], 2)
        
        # Step 4: Mock search operations
        mock_search_results = [
            {
                "id": "LEAD001",
                "content": flattened_texts[0],
                "metadata": {"companyName": company_name, "id": "LEAD001"},
                "score": 0.95
            }
        ]
        
        self.assertEqual(len(mock_search_results), 1)
        self.assertEqual(mock_search_results[0]["id"], "LEAD001")

if __name__ == "__main__":
    unittest.main()
