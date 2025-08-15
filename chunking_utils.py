#!/usr/bin/env python3
"""
Chunking Utilities Module
Functions for processing individual leads and creating optimal chunks for embedding.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from flatten_utils import flattenLeadToText

logger = logging.getLogger(__name__)

# Optimal chunk size for embeddings (2-5KB in characters)
OPTIMAL_CHUNK_SIZE_MIN = 2000  # 2KB
OPTIMAL_CHUNK_SIZE_MAX = 5000  # 5KB

def create_lead_text(lead: Dict[str, Any], company_name: str) -> str:
    """
    Create text content from a single lead.
    
    Args:
        lead: Lead dictionary
        company_name: Company name
        
    Returns:
        str: Text content for the lead
    """
    try:
        # Get the flattened lead text
        lead_text = flattenLeadToText(lead, company_name)
        
        # Add lead identifier
        lead_id = lead.get('id', 'unknown')
        assignee = lead.get('assignedTo', 'Unassigned')
        
        formatted_text = f"Lead ID: {lead_id}\nAssigned To: {assignee}\nCompany: {company_name}\n\n{lead_text}"
        
        return formatted_text
        
    except Exception as e:
        logger.warning(f"Error creating text for lead {lead.get('id', 'unknown')}: {e}")
        # Return basic info as fallback
        lead_id = lead.get('id', 'unknown')
        assignee = lead.get('assignedTo', 'Unassigned')
        return f"Lead ID: {lead_id}\nAssigned To: {assignee}\nCompany: {company_name}\n\n(Error processing lead content)"

def split_text_into_chunks(text: str, max_chunk_size: int = OPTIMAL_CHUNK_SIZE_MAX) -> List[str]:
    """
    Split text into chunks while preserving content structure.
    
    Args:
        text: The text to split
        max_chunk_size: Maximum size for each chunk
        
    Returns:
        List[str]: List of text chunks
    """
    if len(text) <= max_chunk_size:
        return [text]
    
    # For individual leads, split by paragraphs first
    chunks = split_by_paragraphs(text, max_chunk_size)
    
    logger.info(f"Split text ({len(text)} chars) into {len(chunks)} chunks")
    return chunks

def split_by_paragraphs(text: str, max_chunk_size: int) -> List[str]:
    """
    Split text by paragraphs when lead boundaries are not available.
    
    Args:
        text: Text to split
        max_chunk_size: Maximum chunk size
        
    Returns:
        List[str]: List of chunks
    """
    chunks = []
    current_chunk = ""
    
    # Split by double newlines (paragraphs)
    paragraphs = text.split("\n\n")
    
    for paragraph in paragraphs:
        if len(current_chunk) + len(paragraph) + 2 <= max_chunk_size:  # +2 for \n\n
            if current_chunk:
                current_chunk += "\n\n" + paragraph
            else:
                current_chunk = paragraph
        else:
            # Save current chunk and start new one
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            
            # If single paragraph is too large, split by sentences
            if len(paragraph) > max_chunk_size:
                sentence_chunks = split_by_sentences(paragraph, max_chunk_size)
                chunks.extend(sentence_chunks[:-1])  # Add all but last
                current_chunk = sentence_chunks[-1] if sentence_chunks else ""
            else:
                current_chunk = paragraph
    
    # Add the last chunk
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    return chunks

def split_by_sentences(text: str, max_chunk_size: int) -> List[str]:
    """
    Split text by sentences as a last resort.
    
    Args:
        text: Text to split
        max_chunk_size: Maximum chunk size
        
    Returns:
        List[str]: List of chunks
    """
    chunks = []
    current_chunk = ""
    
    # Simple sentence splitting (could be improved with nltk)
    sentences = text.replace(".", ".\n").split("\n")
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
            
        if len(current_chunk) + len(sentence) + 1 <= max_chunk_size:
            if current_chunk:
                current_chunk += " " + sentence
            else:
                current_chunk = sentence
        else:
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            
            # If single sentence is too large, hard split
            if len(sentence) > max_chunk_size:
                words = sentence.split()
                word_chunk = ""
                for word in words:
                    if len(word_chunk) + len(word) + 1 <= max_chunk_size:
                        if word_chunk:
                            word_chunk += " " + word
                        else:
                            word_chunk = word
                    else:
                        if word_chunk.strip():
                            chunks.append(word_chunk.strip())
                        word_chunk = word
                current_chunk = word_chunk
            else:
                current_chunk = sentence
    
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    return chunks

def prepare_record_for_pinecone(record):
    """Flatten the record into a text blob and create metadata for filtering."""
    # Format date fields properly
    created_at = format_date_field(record.get('generatedAt'))
    updated_at = format_date_field(record.get('updatedAt'))
    
    # Get timestamps for metadata filtering
    created_at_timestamp = format_date_for_metadata(record.get('generatedAt'))
    updated_at_timestamp = format_date_for_metadata(record.get('updatedAt'))
    
    text_blob = f"""
    Project Name: {record.get('projectName', '')}
    Project Category: {record.get('projectCategory', '')}
    Project Stage: {record.get('projectStage', '')}
    City: {record.get('projectCity', '')}
    State: {record.get('projectState', '')}
    Concern Person: {record.get('concernPerson', '')}
    Assigned To: {record.get('assignedTo', '')}
    Follow Ups: {record.get('followUp', '')}
    Project Notes: {record.get('projectNotes', '')}
    Lead ID: {record.get('id', '')}
    Phone: {record.get('phone', '')}
    Email: {record.get('email', '')}
    Address: {record.get('address', '')}
    Contact Person: {record.get('contactPerson', '')}
    Lead Source: {record.get('leadSource', '')}
    Priority: {record.get('priority', '')}
    Budget: {record.get('budget', '')}
    Timeline: {record.get('timeline', '')}
    Requirements: {record.get('requirements', '')}
    Status: {record.get('status', '')}
    Next Action: {record.get('nextAction', '')}
    Created At: {created_at}
    Updated At: {updated_at}
    """
    
    metadata = {
        "assignedTo": record.get('assignedTo', ''),
        "projectStage": record.get('projectStage', ''),
        "city": record.get('projectCity', ''),
        "state": record.get('projectState', ''),
        "createdAt": created_at_timestamp,
        "updatedAt": updated_at_timestamp,
        "concernPerson": record.get('concernPerson', ''),
        "projectCategory": record.get('projectCategory', ''),
        "leadSource": record.get('leadSource', ''),
        "priority": record.get('priority', ''),
        "status": record.get('status', ''),
        "phone": record.get('phone', ''),
        "email": record.get('email', '')
    }
    return text_blob.strip(), metadata

def create_chunked_documents(
    leads: List[Dict[str, Any]], 
    company_name: str
) -> List[Dict[str, Any]]:
    """
    Create documents for individual leads using the Pinecone format.
    
    Args:
        leads: List of lead dictionaries
        company_name: Company name
        
    Returns:
        List[Dict[str, Any]]: List of document chunks with metadata
    """
    documents = []
    
    for lead_index, lead in enumerate(leads):
        try:
            lead_id = lead.get('id', f'lead_{lead_index}')
            
            # Use the new prepare_record_for_pinecone format
            text_blob, metadata = prepare_record_for_pinecone(lead)
            
            # Create document ID
            doc_id = f"{company_name}_{lead_id}"
            
            # Add company and lead_id to metadata
            metadata['company'] = company_name
            metadata['lead_id'] = lead_id
            
            documents.append({
                "id": doc_id,
                "chunk_text": text_blob,
                "metadata": metadata
            })
        
        except Exception as e:
            logger.error(f"Error processing lead {lead.get('id', lead_index)}: {e}")
            continue
    
    logger.info(f"Created {len(documents)} documents from {len(leads)} leads")
    return documents

def format_date_field(date_value: Any) -> str:
    """Format date field to string for display."""
    if not date_value:
        return ""
    
    # Handle Firebase DatetimeWithNanoseconds objects
    if hasattr(date_value, 'strftime'):
        try:
            return date_value.isoformat()
        except:
            return str(date_value)
    elif isinstance(date_value, str):
        return date_value.strip()
    else:
        return str(date_value)

def format_date_for_metadata(date_value: Any) -> int:
    """Format date field to Unix timestamp for Pinecone metadata filtering."""
    if not date_value:
        return 0
    
    import datetime
    
    # Handle Firebase DatetimeWithNanoseconds objects
    if hasattr(date_value, 'timestamp'):
        try:
            return int(date_value.timestamp())
        except:
            pass
    
    if hasattr(date_value, 'strftime'):
        try:
            return int(date_value.timestamp())
        except:
            pass
    
    # Handle string dates
    if isinstance(date_value, str):
        try:
            # Try parsing ISO format
            dt = datetime.datetime.fromisoformat(date_value.replace('Z', '+00:00'))
            return int(dt.timestamp())
        except:
            try:
                # Try other common formats
                dt = datetime.datetime.strptime(date_value, "%Y-%m-%d")
                return int(dt.timestamp())
            except:
                return 0
    
    return 0


