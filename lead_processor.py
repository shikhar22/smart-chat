#!/usr/bin/env python3
"""
Lead Processing Module
Functions to process and flatten lead data for embedding and vector storage.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def flatten_lead_to_text(lead: dict, company: str) -> str:
    """
    Convert a lead dictionary into a clean plain-text paragraph for embedding.
    
    Args:
        lead (dict): The lead data dictionary
        company (str): The company name
        
    Returns:
        str: A natural language paragraph describing the lead
    """
    # Start with the company line
    text_parts = [f"Lead from {company}"]
    
    # Priority fields to extract and their display names
    priority_fields = [
        # Field path, display name
        ("enquiryDate", "Enquiry Date"),
        ("clientDetails.city", "City"),
        ("projectStage", "Project Stage"),
        ("clientDetails.name", "Client Name"),
        ("lastContactDate", "Last Contact Date"),
        ("lastDiscussion", "Last Discussion"),
        ("nextSteps", "Next Steps"),
        # Additional fields that might be useful
        ("concernPerson", "Contact Person"),
        ("status", "Status"),
        ("projectCategory", "Project Category"),
        ("clientDetails.phoneNumber", "Phone Number"),
        ("assignedTo", "Assigned To"),
        ("createdBy", "Created By"),
        ("updatedAt", "Last Updated"),
        ("createdAt", "Created Date")
    ]
    
    def get_nested_value(data: dict, path: str) -> Any:
        """Get value from nested dictionary using dot notation."""
        keys = path.split('.')
        value = data
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        return value
    
    def is_empty_value(value: Any) -> bool:
        """Check if a value is empty, null, or a default value."""
        if value is None:
            return True
        if isinstance(value, str):
            return value.strip() == "" or value.lower() in ["n/a", "na", "null", "none", "-", "tbd", "pending"]
        if isinstance(value, (list, dict)):
            return len(value) == 0
        if isinstance(value, (int, float)):
            return value == 0
        return False
    
    def format_date(date_value: Any) -> str:
        """Format date value to a readable string."""
        if is_empty_value(date_value):
            return None
            
        # If it's already a string, try to parse and reformat
        if isinstance(date_value, str):
            try:
                # Try parsing common date formats
                for fmt in ["%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%fZ"]:
                    try:
                        date_obj = datetime.strptime(date_value.replace("Z", ""), fmt.replace(".%fZ", ""))
                        return date_obj.strftime("%B %d, %Y")
                    except ValueError:
                        continue
                # If parsing fails, return the original string if it's not empty
                return date_value if date_value.strip() else None
            except:
                return date_value if date_value.strip() else None
        
        return str(date_value)
    
    # Process priority fields
    for field_path, display_name in priority_fields:
        value = get_nested_value(lead, field_path)
        
        if not is_empty_value(value):
            # Special handling for dates
            if "date" in field_path.lower() or "Date" in display_name:
                formatted_value = format_date(value)
                if formatted_value:
                    text_parts.append(f"{display_name}: {formatted_value}")
            else:
                text_parts.append(f"{display_name}: {value}")
    
    # Add any other interesting fields that weren't covered
    additional_fields = {}
    for key, value in lead.items():
        if key not in ["id", "clientDetails"] and not is_empty_value(value):
            # Skip fields we already processed
            processed_keys = [path.split('.')[0] for path, _ in priority_fields]
            if key not in processed_keys:
                if isinstance(value, dict):
                    # For nested objects, extract key information
                    for sub_key, sub_value in value.items():
                        if not is_empty_value(sub_value):
                            additional_fields[f"{key}.{sub_key}"] = sub_value
                else:
                    additional_fields[key] = value
    
    # Add selected additional fields
    for key, value in additional_fields.items():
        if len(text_parts) < 15:  # Limit to avoid too long text
            text_parts.append(f"{key.replace('.', ' ')}: {value}")
    
    # Join all parts into a natural paragraph
    if len(text_parts) == 1:  # Only company name
        text_parts.append("No detailed information available for this lead.")
    
    return ". ".join(text_parts) + "."

def process_leads_for_embedding(leads: List[Dict[str, Any]], company: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Process leads and group them by createdById and assignedToId, creating documents ready for embedding.
    
    Args:
        leads (List[Dict[str, Any]]): List of lead dictionaries from Firebase
        company (str): The company name
        
    Returns:
        Dict[str, List[Dict[str, Any]]]: Dictionary with combined grouping keys and lists of documents as values
    """
    grouped_leads = {}
    
    for lead in leads:
        # Get createdById and assignedToId, use 'unknown' if not present
        created_by_id = lead.get('createdById', 'unknown')
        assigned_to_id = lead.get('assignedToId', 'unassigned')
        
        # Get names for better readability
        created_by = lead.get('createdBy', '')
        assigned_to = lead.get('assignedTo', '')
        
        # Get other metadata
        lead_id = lead.get('id', lead.get('leadId', ''))
        city = ""
        updated_at = lead.get('updatedAt', lead.get('updated_at', ''))
        
        # Extract city from various possible locations
        if 'clientDetails' in lead and isinstance(lead['clientDetails'], dict):
            city = lead['clientDetails'].get('city', '')
        elif 'city' in lead:
            city = lead['city']
        
        # Create the flattened text
        flattened_text = flatten_lead_to_text(lead, company)
        
        # Create a combined grouping key that includes both creator and assignee
        grouping_key = f"created:{created_by_id}|assigned:{assigned_to_id}"
        
        # Create document structure with enhanced metadata
        document = {
            'id': lead_id,
            'text': flattened_text,
            'metadata': {
                'company': company,
                'leadId': lead_id,
                'createdById': created_by_id,
                'createdBy': created_by,
                'assignedToId': assigned_to_id,
                'assignedTo': assigned_to,
                'city': city,
                'updatedAt': updated_at,
                'groupingKey': grouping_key
            }
        }
        
        # Group by the combined key
        if grouping_key not in grouped_leads:
            grouped_leads[grouping_key] = []
        
        grouped_leads[grouping_key].append(document)
    
    logger.info(f"Processed {len(leads)} leads into {len(grouped_leads)} groups by creator and assignee for company {company}")
    
    return grouped_leads

def prepare_documents_for_vector_store(grouped_leads: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """
    Flatten the grouped leads into a single list of documents ready for vector store upsertion.
    
    Args:
        grouped_leads (Dict[str, List[Dict[str, Any]]]): Grouped leads by createdById
        
    Returns:
        List[Dict[str, Any]]: List of documents ready for embedding
    """
    documents = []
    
    for created_by_id, lead_docs in grouped_leads.items():
        documents.extend(lead_docs)
    
    return documents

def get_processing_summary(grouped_leads: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    """
    Get a summary of the lead processing results.
    
    Args:
        grouped_leads (Dict[str, List[Dict[str, Any]]]): Grouped leads by creator and assignee
        
    Returns:
        Dict[str, Any]: Summary statistics
    """
    total_leads = sum(len(leads) for leads in grouped_leads.values())
    
    # Extract individual creators and assignees for analysis
    creators = set()
    assignees = set()
    creator_lead_counts = {}
    assignee_lead_counts = {}
    
    for grouping_key, leads in grouped_leads.items():
        # Parse the grouping key to extract creator and assignee IDs
        parts = grouping_key.split('|')
        created_by_id = parts[0].replace('created:', '') if len(parts) > 0 else 'unknown'
        assigned_to_id = parts[1].replace('assigned:', '') if len(parts) > 1 else 'unassigned'
        
        creators.add(created_by_id)
        assignees.add(assigned_to_id)
        
        # Count leads by creator
        creator_lead_counts[created_by_id] = creator_lead_counts.get(created_by_id, 0) + len(leads)
        
        # Count leads by assignee
        assignee_lead_counts[assigned_to_id] = assignee_lead_counts.get(assigned_to_id, 0) + len(leads)
    
    summary = {
        'total_leads_processed': total_leads,
        'total_groups': len(grouped_leads),
        'total_unique_creators': len(creators),
        'total_unique_assignees': len(assignees),
        'leads_by_creator': creator_lead_counts,
        'leads_by_assignee': assignee_lead_counts,
        'leads_by_group': {grouping_key: len(leads) for grouping_key, leads in grouped_leads.items()},
        'creators_list': list(creators),
        'assignees_list': list(assignees),
        'grouping_keys': list(grouped_leads.keys())
    }
    
    return summary
