#!/usr/bin/env python3
"""
Test script for the Firebase update-data endpoint
Demonstrates the functionality of the new /update-data endpoint.
"""

import requests
import json
from typing import Dict, Any

def test_update_data_endpoint(base_url: str = "http://localhost:8008"):
    """Test the /update-data endpoint with different scenarios."""
    
    print("🚀 Testing FastAPI /update-data endpoint\n")
    
    # Test cases
    test_cases = [
        {
            "name": "Valid company (Kalco)",
            "company": "Kalco",
            "expected_status": 200
        },
        {
            "name": "Invalid company",
            "company": "NonExistent",
            "expected_status": 404
        }
    ]
    
    for test_case in test_cases:
        print(f"📋 {test_case['name']}")
        print(f"   Company: {test_case['company']}")
        
        try:
            response = requests.post(
                f"{base_url}/update-data",
                json={"company": test_case["company"]},
                headers={"Content-Type": "application/json"}
            )
            
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == test_case["expected_status"]:
                print("   ✅ Expected status code")
            else:
                print(f"   ❌ Unexpected status code (expected {test_case['expected_status']})")
            
            # Parse response
            try:
                response_data = response.json()
                if response.status_code == 200:
                    print(f"   📊 Fetched {response_data.get('leads_count', 0)} leads")
                    print(f"   📝 Message: {response_data.get('message', 'N/A')}")
                else:
                    print(f"   ⚠️  Error: {response_data.get('detail', 'Unknown error')}")
            except json.JSONDecodeError:
                print("   ❌ Invalid JSON response")
            
        except requests.RequestException as e:
            print(f"   ❌ Request failed: {str(e)}")
        
        print()  # Empty line for readability

def test_firebase_client_directly():
    """Test the Firebase client utility functions directly."""
    
    print("🔧 Testing Firebase client utility functions\n")
    
    try:
        from firebase_client import (
            get_firebase_companies, 
            validate_firebase_company,
            fetch_company_leads
        )
        
        # Test available companies
        companies = get_firebase_companies()
        print(f"📁 Available companies: {companies}")
        
        # Test validation
        for company in ["Kalco", "NonExistent"]:
            is_valid = validate_firebase_company(company)
            status = "✅ Valid" if is_valid else "❌ Invalid"
            print(f"   {company}: {status}")
        
        # Test fetching leads for Kalco (if available)
        if "Kalco" in companies:
            try:
                leads = fetch_company_leads("Kalco")
                print(f"   📊 Kalco leads count: {len(leads)}")
                if leads:
                    # Show first lead structure (without sensitive data)
                    first_lead = leads[0]
                    print(f"   📋 Sample lead keys: {list(first_lead.keys())[:5]}...")
            except Exception as e:
                print(f"   ❌ Error fetching Kalco leads: {str(e)}")
        
    except ImportError as e:
        print(f"❌ Failed to import Firebase client: {str(e)}")
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")

if __name__ == "__main__":
    print("=" * 60)
    print("Firebase Update Data Endpoint Test Suite")
    print("=" * 60)
    print()
    
    # Test the FastAPI endpoint
    test_update_data_endpoint()
    
    print("-" * 40)
    print()
    
    # Test Firebase client directly
    test_firebase_client_directly()
    
    print()
    print("✨ Test suite completed!")
    print("=" * 60)
