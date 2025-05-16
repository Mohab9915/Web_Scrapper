"""
Utility functions for text processing.
"""
import re
import json
from typing import List, Dict, Any
import tiktoken

async def structure_scraped_data(markdown_content: str) -> Dict[str, Any]:
    """
    Structure scraped markdown content into a more usable format.
    
    In a real implementation, this might use an LLM to extract structured data.
    
    Args:
        markdown_content (str): Markdown content
        
    Returns:
        Dict[str, Any]: Structured data
    """
    # Extract title (first h1)
    title_match = re.search(r'# (.*?)(\n|$)', markdown_content)
    title = title_match.group(1) if title_match else "Untitled"
    
    # Extract sections
    sections = []
    current_section = None
    
    for line in markdown_content.split('\n'):
        if line.startswith('## '):
            if current_section:
                sections.append(current_section)
            current_section = {"heading": line[3:], "content": ""}
        elif line.startswith('# '):
            # Skip h1 (title)
            continue
        elif current_section:
            current_section["content"] += line + "\n"
    
    if current_section:
        sections.append(current_section)
    
    # Extract bullet points
    bullet_points = re.findall(r'- (.*?)(\n|$)', markdown_content)
    bullet_points = [bp[0] for bp in bullet_points]
    
    # Create structured data
    structured_data = {
        "title": title,
        "sections": sections,
        "bullet_points": bullet_points,
        "full_content": markdown_content
    }
    
    return structured_data

async def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """
    Split text into chunks for embedding.
    
    Args:
        text (str): The text to chunk
        chunk_size (int): Target size of each chunk in characters
        overlap (int): Number of characters to overlap between chunks
    
    Returns:
        List[str]: List of text chunks
    """
    # In a real implementation, this would be more sophisticated
    # and would use tiktoken to count tokens
    
    # Simple chunking by paragraphs
    paragraphs = text.split('\n\n')
    chunks = []
    current_chunk = ""
    
    for paragraph in paragraphs:
        if len(current_chunk) + len(paragraph) <= chunk_size:
            current_chunk += paragraph + "\n\n"
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = paragraph + "\n\n"
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks
