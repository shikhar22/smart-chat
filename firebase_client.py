#!/usr/bin/env python3
"""
Firebase Client Utility
Provides Firebase initialization and data fetching functionality for different companies.
"""

import json
import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import firebase_admin
from firebase_admin import credentials, firestore

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FirebaseClientManager:
    """Manages Firebase client connections for different companies."""
    
    def __init__(self):
        """Initialize the Firebase client manager."""
        self._apps = {}  # Store Firebase app instances by company name
        self._db_clients = {}  # Store Firestore clients by company name
        self.firebase_config_dir = Path(__file__).parent / "firebase_config"
        
    def _get_service_account_path(self, company_name: str) -> Path:
        """Get the service account key file path for a company."""
        return self.firebase_config_dir / f"{company_name}.json"
    
    def _initialize_firebase_app(self, company_name: str) -> firebase_admin.App:
        """Initialize Firebase app for a specific company."""
        if company_name in self._apps:
            return self._apps[company_name]
        
        service_account_path = self._get_service_account_path(company_name)
        
        if not service_account_path.exists():
            raise FileNotFoundError(
                f"Firebase service account key not found for company '{company_name}'. "
                f"Expected file: {service_account_path}"
            )
        
        try:
            # Load service account credentials
            cred = credentials.Certificate(str(service_account_path))
            
            # Initialize the app with a unique name
            app_name = f"{company_name}_app"
            app = firebase_admin.initialize_app(cred, name=app_name)
            
            self._apps[company_name] = app
            logger.info(f"Firebase app initialized for company: {company_name}")
            
            return app
            
        except Exception as e:
            logger.error(f"Failed to initialize Firebase app for {company_name}: {str(e)}")
            raise Exception(f"Firebase initialization failed for {company_name}: {str(e)}")
    
    def _get_firestore_client(self, company_name: str) -> firestore.Client:
        """Get Firestore client for a specific company."""
        if company_name in self._db_clients:
            return self._db_clients[company_name]
        
        # Initialize Firebase app if not already done
        app = self._initialize_firebase_app(company_name)
        
        # Create Firestore client
        db = firestore.client(app=app)
        self._db_clients[company_name] = db
        
        return db
    
    def fetch_leads(self, company_name: str) -> List[Dict[str, Any]]:
        """
        Fetch leads collection from Firebase for a specific company.
        
        Args:
            company_name: The name of the company
            
        Returns:
            List of lead documents as dictionaries
            
        Raises:
            FileNotFoundError: If service account key file is not found
            Exception: If Firebase operation fails
        """
        try:
            # Get Firestore client for the company
            db = self._get_firestore_client(company_name)
            
            # Fetch leads collection
            leads_ref = db.collection('leads')
            docs = leads_ref.stream()
            
            leads = []
            for doc in docs:
                lead_data = doc.to_dict()
                lead_data['id'] = doc.id  # Include document ID
                leads.append(lead_data)
            
            logger.info(f"Fetched {len(leads)} leads for company: {company_name}")
            return leads
            
        except FileNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to fetch leads for {company_name}: {str(e)}")
            raise Exception(f"Failed to fetch leads for {company_name}: {str(e)}")
    
    def get_available_companies(self) -> List[str]:
        """
        Get list of companies that have Firebase configuration files.
        
        Returns:
            List of company names that have service account keys
        """
        if not self.firebase_config_dir.exists():
            return []
        
        companies = []
        for file_path in self.firebase_config_dir.glob("*.json"):
            company_name = file_path.stem
            companies.append(company_name)
        
        return sorted(companies)
    
    def validate_company_config(self, company_name: str) -> bool:
        """
        Validate if a company has a proper Firebase configuration file.
        
        Args:
            company_name: The name of the company to validate
            
        Returns:
            True if configuration exists and is valid, False otherwise
        """
        service_account_path = self._get_service_account_path(company_name)
        
        if not service_account_path.exists():
            return False
        
        try:
            with open(service_account_path, 'r') as f:
                config = json.load(f)
                
            # Check if required fields are present
            required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email']
            return all(field in config for field in required_fields)
            
        except (json.JSONDecodeError, IOError):
            return False
    
    def cleanup(self):
        """Clean up Firebase app instances."""
        for company_name, app in self._apps.items():
            try:
                firebase_admin.delete_app(app)
                logger.info(f"Cleaned up Firebase app for company: {company_name}")
            except Exception as e:
                logger.warning(f"Failed to cleanup Firebase app for {company_name}: {str(e)}")
        
        self._apps.clear()
        self._db_clients.clear()

# Global instance
firebase_manager = FirebaseClientManager()

def fetch_company_leads(company_name: str) -> List[Dict[str, Any]]:
    """
    Utility function to fetch leads for a specific company.
    
    Args:
        company_name: The name of the company
        
    Returns:
        List of lead documents as dictionaries
    """
    return firebase_manager.fetch_leads(company_name)

def get_firebase_companies() -> List[str]:
    """
    Utility function to get available companies with Firebase configuration.
    
    Returns:
        List of company names
    """
    return firebase_manager.get_available_companies()

def validate_firebase_company(company_name: str) -> bool:
    """
    Utility function to validate company Firebase configuration.
    
    Args:
        company_name: The name of the company to validate
        
    Returns:
        True if configuration is valid, False otherwise
    """
    return firebase_manager.validate_company_config(company_name)
