#!/usr/bin/env python3
"""
Flatten Utilities Module
Functions to convert lead data into text format for embedding.
"""

from typing import Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def flattenLeadToText(lead: dict, company_name: str) -> str:
    """
    Convert a lead dictionary into a readable text summary for embedding.
    
    Args:
        lead: The lead data dictionary
        company_name: The name of the company
        
    Returns:
        str: A readable text summary of the lead
    """
    # Start with the company identifier
    text_parts = [f"Lead from {company_name}: id={lead.get('id', 'unknown')}."]
    
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
        """Check if a value is empty, null, or a placeholder."""
        if value is None:
            return True
        if isinstance(value, str):
            stripped = value.strip().lower()
            return (stripped == "" or 
                   stripped in ["n/a", "na", "null", "none", "-", "tbd", "pending", "--select--"])
        if isinstance(value, (list, dict)):
            return len(value) == 0
        # Handle Firebase DatetimeWithNanoseconds and other datetime objects
        try:
            # If it's a datetime-like object, it's not empty
            if hasattr(value, 'strftime') or hasattr(value, 'isoformat'):
                return False
        except:
            pass
        return False
    
    def format_date(date_value: Any) -> str:
        """Format date value to a readable string."""
        if is_empty_value(date_value):
            return None
        
        # Handle Firebase DatetimeWithNanoseconds and other datetime objects
        if hasattr(date_value, 'strftime'):
            try:
                return date_value.strftime("%B %d, %Y")
            except:
                # Fallback to string representation
                return str(date_value)
        
        # Handle string dates        
        if isinstance(date_value, str):
            try:
                # Try parsing common date formats
                for fmt in ["%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%fZ"]:
                    try:
                        date_obj = datetime.strptime(date_value.replace("Z", ""), fmt.replace(".%fZ", ""))
                        return date_obj.strftime("%B %d, %Y")
                    except ValueError:
                        continue
                # If parsing fails, return the original if it's meaningful
                return date_value if date_value.strip() else None
            except:
                return date_value if date_value.strip() else None
        
        return str(date_value)
    
    # Extract key fields to include
    fields_to_extract = [
        ("generatedAt", "Enquiry Date", format_date),
        ("projectName", "Project", str),
        ("projectCity", "City", str),
        ("projectStage", "Stage", str),
        ("projectCategory", "Category", str),
        ("projectSource", "Source", str),
        ("clientDetails.name", "Client", str),
        ("clientDetails.phoneNumber", "Phone", str),
        ("lastContactDate", "Last Contact", format_date),
        ("lastDiscussion", "Last Discussion", str),
        ("nextFollowUpDate", "Next Follow-up", format_date),
        ("updatedAt", "Updated", format_date),
    ]
    
    # Process each field
    for field_path, display_name, formatter in fields_to_extract:
        value = get_nested_value(lead, field_path)
        
        if not is_empty_value(value):
            try:
                formatted_value = formatter(value)
                if formatted_value and not is_empty_value(formatted_value):
                    text_parts.append(f"{display_name}: {formatted_value}")
            except Exception as e:
                logger.warning(f"Error formatting field {field_path}: {e}")
                # Use raw value as fallback
                if value and not is_empty_value(value):
                    text_parts.append(f"{display_name}: {value}")
    
    # Add follow-up summary if we have follow-up related data
    followup_parts = []
    
    last_contact = get_nested_value(lead, "lastContactDate")
    if not is_empty_value(last_contact):
        formatted_contact = format_date(last_contact)
        if formatted_contact:
            followup_parts.append(f"last contacted {formatted_contact}")
    
    last_discussion = get_nested_value(lead, "lastDiscussion")
    if not is_empty_value(last_discussion):
        followup_parts.append(f"discussed: {last_discussion}")
    
    next_followup = get_nested_value(lead, "nextFollowUpDate")
    if not is_empty_value(next_followup):
        formatted_followup = format_date(next_followup)
        if formatted_followup:
            followup_parts.append(f"next follow-up scheduled for {formatted_followup}")
    
    if followup_parts:
        text_parts.append(f"Follow-up summary: {', '.join(followup_parts)}")
    
    # Join all parts with appropriate separators
    return ". ".join(text_parts) + "."
