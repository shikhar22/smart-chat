#!/usr/bin/env python3
"""
Chunking Utilities Module
Functions for grouping leads by assignee and creating optimal chunks for embedding.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from flatten_utils import flattenLeadToText

logger = logging.getLogger(__name__)

# Optimal chunk size for embeddings (2-5KB in characters)
OPTIMAL_CHUNK_SIZE_MIN = 2000  # 2KB
OPTIMAL_CHUNK_SIZE_MAX = 5000  # 5KB

def group_leads_by_assignee(leads: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Group leads by assignedTo field.
    
    Args:
        leads: List of lead dictionaries
        
    Returns:
        Dict[str, List[Dict[str, Any]]]: Dictionary with assignedTo as key and list of leads as value
    """
    grouped_leads = {}
    unassigned_leads = []
    
    for lead in leads:
        assigned_to = lead.get('assignedTo', '')
        
        # Handle different data types safely
        if isinstance(assigned_to, str):
            assigned_to = assigned_to.strip()
        else:
            assigned_to = str(assigned_to) if assigned_to else ''
        
        if not assigned_to or assigned_to.lower() in ['', 'null', 'none', 'n/a', 'unassigned']:
            unassigned_leads.append(lead)
        else:
            if assigned_to not in grouped_leads:
                grouped_leads[assigned_to] = []
            grouped_leads[assigned_to].append(lead)
    
    # Add unassigned leads under a special key
    if unassigned_leads:
        grouped_leads['Unassigned'] = unassigned_leads
    
    logger.info(f"Grouped leads into {len(grouped_leads)} assignee groups")
    for assignee, assignee_leads in grouped_leads.items():
        logger.info(f"  - {assignee}: {len(assignee_leads)} leads")
    
    return grouped_leads

def create_rich_text_block(leads: List[Dict[str, Any]], company_name: str, assignee: str) -> str:
    """
    Create a rich text block from multiple leads for a single assignee.
    
    Args:
        leads: List of leads for this assignee
        company_name: Company name
        assignee: Assignee name
        
    Returns:
        str: Rich text block containing all leads information
    """
    text_parts = [
        f"Sales Portfolio for {assignee} at {company_name}",
        f"Total Leads: {len(leads)}",
        "=" * 50
    ]
    
    for i, lead in enumerate(leads, 1):
        try:
            # Get the flattened lead text
            lead_text = flattenLeadToText(lead, company_name)
            
            # Add lead header with number
            text_parts.append(f"\nLead #{i}:")
            text_parts.append(lead_text)
            text_parts.append("-" * 30)
            
        except Exception as e:
            logger.warning(f"Error flattening lead {lead.get('id', 'unknown')}: {e}")
            # Add basic info as fallback
            text_parts.append(f"\nLead #{i}: {lead.get('id', 'unknown')} (processing error)")
            text_parts.append("-" * 30)
    
    return "\n".join(text_parts)

def split_text_into_chunks(text: str, max_chunk_size: int = OPTIMAL_CHUNK_SIZE_MAX) -> List[str]:
    """
    Split text into chunks while trying to preserve lead boundaries.
    
    Args:
        text: The text to split
        max_chunk_size: Maximum size for each chunk
        
    Returns:
        List[str]: List of text chunks
    """
    if len(text) <= max_chunk_size:
        return [text]
    
    chunks = []
    
    # Split by lead boundaries first (look for "Lead #" pattern)
    lead_sections = text.split("\nLead #")
    
    if len(lead_sections) <= 1:
        # No clear lead boundaries, split by paragraphs
        return split_by_paragraphs(text, max_chunk_size)
    
    # Reconstruct first section (header)
    current_chunk = lead_sections[0]
    
    for i, section in enumerate(lead_sections[1:], 1):
        # Add back the "Lead #" prefix
        section = f"\nLead #{section}"
        
        # Check if adding this section would exceed the limit
        if len(current_chunk) + len(section) <= max_chunk_size:
            current_chunk += section
        else:
            # Save current chunk and start new one
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            current_chunk = section
    
    # Add the last chunk
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    # If any chunk is still too large, split it further
    final_chunks = []
    for chunk in chunks:
        if len(chunk) <= max_chunk_size:
            final_chunks.append(chunk)
        else:
            # Split oversized chunks by paragraphs
            sub_chunks = split_by_paragraphs(chunk, max_chunk_size)
            final_chunks.extend(sub_chunks)
    
    logger.info(f"Split text ({len(text)} chars) into {len(final_chunks)} chunks")
    return final_chunks

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

def create_chunked_documents(
    grouped_leads: Dict[str, List[Dict[str, Any]]], 
    company_name: str
) -> List[Dict[str, Any]]:
    """
    Create chunked documents for all assignee groups.
    
    Args:
        grouped_leads: Dictionary of assignee -> leads
        company_name: Company name
        
    Returns:
        List[Dict[str, Any]]: List of document chunks with metadata
    """
    documents = []
    
    for assignee, leads in grouped_leads.items():
        try:
            # Create rich text block for this assignee
            rich_text = create_rich_text_block(leads, company_name, assignee)
            
            # Split into optimal chunks
            chunks = split_text_into_chunks(rich_text)
            
            # Get common metadata from the leads
            assignee_id = get_most_common_value(leads, 'assignedToId')
            latest_generated_at = get_latest_date(leads, 'generatedAt')
            latest_updated_at = get_latest_date(leads, 'updatedAt')
            project_cities = get_unique_values(leads, 'projectCity')
            project_categories = get_unique_values(leads, 'projectCategory')
            project_stages = get_unique_values(leads, 'projectStage')
            project_sources = get_unique_values(leads, 'projectSource')
            
            # Create document for each chunk
            for chunk_index, chunk_text in enumerate(chunks):
                doc_id = f"{company_name}_{assignee}_{chunk_index}"
                
                metadata = {
                    "assignedTo": assignee,
                    "assignedToId": assignee_id or "",
                    "company": company_name,
                    "generatedAt": latest_generated_at or "",
                    "updatedAt": latest_updated_at or "",
                    "projectCity": ", ".join(project_cities) if project_cities else "",
                    "projectCategory": ", ".join(project_categories) if project_categories else "",
                    "projectStage": ", ".join(project_stages) if project_stages else "",
                    "projectSource": ", ".join(project_sources) if project_sources else "",
                    "chunk_index": chunk_index,
                    "total_chunks": len(chunks),
                    "total_leads": len(leads),
                    "lead_ids": [lead.get('id', '') for lead in leads]
                }
                
                # Remove empty values
                metadata = {k: v for k, v in metadata.items() if v}
                
                documents.append({
                    "id": doc_id,
                    "text": chunk_text,
                    "metadata": metadata
                })
        
        except Exception as e:
            logger.error(f"Error processing assignee {assignee}: {e}")
            continue
    
    logger.info(f"Created {len(documents)} chunked documents for {len(grouped_leads)} assignees")
    return documents

def get_most_common_value(leads: List[Dict[str, Any]], field: str) -> Optional[str]:
    """Get the most common value for a field across leads."""
    values = []
    for lead in leads:
        value = lead.get(field, '')
        # Handle different data types safely
        if value:
            if isinstance(value, str):
                value = value.strip()
                if value:
                    values.append(value)
            else:
                # Convert non-string values to string
                values.append(str(value))
    
    if not values:
        return None
    
    # Return most common value
    from collections import Counter
    counter = Counter(values)
    return counter.most_common(1)[0][0] if counter else None

def get_latest_date(leads: List[Dict[str, Any]], field: str) -> Optional[str]:
    """Get the latest date value for a field across leads."""
    dates = []
    for lead in leads:
        date_value = lead.get(field, '')
        if date_value:
            # Handle Firebase DatetimeWithNanoseconds objects
            if hasattr(date_value, 'strftime'):
                try:
                    # Convert to ISO string for comparison
                    dates.append(date_value.isoformat())
                except:
                    dates.append(str(date_value))
            elif isinstance(date_value, str):
                date_value = date_value.strip()
                if date_value:
                    dates.append(date_value)
            else:
                dates.append(str(date_value))
    
    if not dates:
        return None
    
    # Simple string comparison should work for ISO dates
    return max(dates)

def get_unique_values(leads: List[Dict[str, Any]], field: str) -> List[str]:
    """Get unique non-empty values for a field across leads."""
    values = set()
    for lead in leads:
        value = lead.get(field, '')
        if value:
            # Handle different data types safely
            if isinstance(value, str):
                value = value.strip()
                if value and value.lower() not in ['', 'null', 'none', 'n/a']:
                    values.add(value)
            else:
                # Convert non-string values to string
                str_value = str(value)
                if str_value and str_value.lower() not in ['', 'null', 'none', 'n/a']:
                    values.add(str_value)
    
    return sorted(list(values))
