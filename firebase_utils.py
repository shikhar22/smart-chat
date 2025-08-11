#!/usr/bin/env python3
"""
Firebase Utilities Module
Provides Firebase initialization and lead fetching functionality.
"""

import json
import logging
from typing import List, Dict, Any
from pathlib import Path
import firebase_admin
from firebase_admin import credentials, firestore

logger = logging.getLogger(__name__)

# Global registry to track initialized Firebase apps
_firebase_apps: Dict[str, firebase_admin.App] = {}

def init_firebase_app(company_name: str) -> firebase_admin.App:
    """
    Initialize Firebase app for a specific company.
    
    Args:
        company_name: The name of the company
        
    Returns:
        firebase_admin.App: The initialized Firebase app instance
        
    Raises:
        FileNotFoundError: If service account key file is not found
        Exception: If Firebase initialization fails
    """
    # Return existing app if already initialized
    if company_name in _firebase_apps:
        return _firebase_apps[company_name]
    
    # Get service account file path
    firebase_config_dir = Path(__file__).parent / "firebase_config"
    service_account_path = firebase_config_dir / f"{company_name}.json"
    
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
        
        # Store in registry
        _firebase_apps[company_name] = app
        
        logger.info(f"Firebase app initialized for company: {company_name}")
        return app
        
    except Exception as e:
        logger.error(f"Failed to initialize Firebase app for {company_name}: {str(e)}")
        raise Exception(f"Firebase initialization failed for {company_name}: {str(e)}")

def fetch_all_leads(company_name: str) -> List[dict]:
    """
    Fetch all leads from Firebase for a specific company.
    
    Args:
        company_name: The name of the company
        
    Returns:
        List[dict]: Plain list of lead dictionaries (no transforms)
        
    Raises:
        FileNotFoundError: If service account key file is not found
        Exception: If Firebase operation fails
    """
    try:
        # Initialize Firebase app
        app = init_firebase_app(company_name)
        
        # Get Firestore client
        db = firestore.client(app=app)
        
        # Fetch leads collection
        leads_ref = db.collection('leads')
        docs = leads_ref.stream()
        
        leads = []
        for doc in docs:
            lead_data = doc.to_dict()
            # Include document ID as id if not already present
            if 'id' not in lead_data:
                lead_data['id'] = doc.id
            leads.append(lead_data)
        
        logger.info(f"Fetched {len(leads)} leads for company: {company_name}")
        return leads
        
    except FileNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch leads for {company_name}: {str(e)}")
        raise Exception(f"Failed to fetch leads for {company_name}: {str(e)}")
