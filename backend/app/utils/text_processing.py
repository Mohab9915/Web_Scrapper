"""
Utility functions for text processing.
"""
import re
import json
import httpx
from typing import List, Dict, Any, Optional
import tiktoken

from ..scraper_modules.assets import AZURE_CHAT_MODEL # Changed to relative import

async def structure_scraped_data(
    markdown_content: str,
    conditions: str = None,
    azure_credentials: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Structure scraped markdown content into a more usable format.

    Extracts data based on specified conditions and returns it in a tabular format.
    If Azure OpenAI credentials are provided, uses LLM for more accurate extraction.

    Args:
        markdown_content (str): Markdown content
        conditions (str, optional): Comma-separated list of fields to extract
        azure_credentials (Dict[str, str], optional): Azure OpenAI credentials for LLM-based extraction

    Returns:
        Dict[str, Any]: Structured data including tabular data
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

    # Extract tabular data based on conditions
    tabular_data = []

    if conditions:
        # Parse conditions into a list of fields
        fields = [field.strip().lower() for field in conditions.split(',')]

        # Check if we can use LLM-based extraction
        if azure_credentials and 'api_key' in azure_credentials and 'endpoint' in azure_credentials:
            print("Using LLM-based extraction for structured data")
            # Use LLM to extract structured data
            llm_tabular_data = await extract_structured_data_with_llm(
                markdown_content,
                fields,
                azure_credentials
            )

            if llm_tabular_data:
                tabular_data = llm_tabular_data
            else:
                print("LLM extraction failed or returned no data, falling back to regex-based extraction")
                # Fall back to regex-based extraction
                tabular_data = await extract_data_with_regex(markdown_content, fields, title, sections, bullet_points)
        else:
            # Use regex-based extraction
            print("Using regex-based extraction for structured data")
            tabular_data = await extract_data_with_regex(markdown_content, fields, title, sections, bullet_points)

    # Add tabular data to the structured data
    structured_data["tabular_data"] = tabular_data

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

async def format_data_for_display(
    tabular_data: List[Dict[str, Any]],
    fields: List[str],
    display_format: str, # This argument is kept for consistency but less used if tabular_data is empty
    full_markdown_content: Optional[str] = None # Added full_markdown_content
) -> Dict[str, Any]:
    """
    Format tabular data for display based on the specified format.
    If tabular_data is empty, provides fallbacks using full_markdown_content for raw view.

    Args:
        tabular_data (List[Dict[str, Any]]): Tabular data to format
        fields (List[str]): List of fields in the data
        display_format (str): Display format ('table', 'paragraph', or 'raw')
        full_markdown_content (Optional[str]): Full raw markdown content of the page

    Returns:
        Dict[str, Any]: Formatted data
    """
    table_data = tabular_data if tabular_data else []
    paragraph_data = ""
    raw_data = ""

    if tabular_data:
        # Format data for paragraph view
        for i, row in enumerate(tabular_data):
            paragraph_data += f"Item {i+1}:\n"
            for field_name in fields: # Iterate using fields to maintain order and selection
                if field_name in row and row[field_name]:
                    paragraph_data += f"{field_name.capitalize()}: {row[field_name]}\n"
            paragraph_data += "\n"

        # Format data for raw view (structured items)
        for i, row in enumerate(tabular_data):
            raw_data += f"--- Item {i+1} ---\n"
            for field_name, value in row.items(): # Show all extracted fields for each item in raw
                if value:
                    raw_data += f"{field_name}: {value}\n"
            raw_data += "\n"
    else:
        # No tabular data extracted
        paragraph_data = "No structured items were extracted from the content."
        if full_markdown_content:
            raw_data = f"---\nNOTE: No structured items were extracted. Displaying full raw markdown content as fallback.\n---\n\n{full_markdown_content}"
        else:
            raw_data = "No structured items were extracted, and no raw markdown content is available."
            
    return {
        "table_data": table_data, # This will be an empty list if tabular_data was empty
        "paragraph_data": paragraph_data.strip(),
        "raw_data": raw_data.strip()
    }

async def extract_data_with_regex(
    markdown_content: str,
    fields: List[str],
    title: str,
    sections: List[Dict[str, str]],
    bullet_points: List[str]
) -> List[Dict[str, Any]]:
    """
    Extract structured data using regex-based approach.

    Args:
        markdown_content (str): The markdown content to process
        fields (List[str]): List of fields to extract
        title (str): Title extracted from the content
        sections (List[Dict[str, str]]): Sections extracted from the content
        bullet_points (List[str]): Bullet points extracted from the content

    Returns:
        List[Dict[str, Any]]: Extracted data in tabular format
    """
    tabular_data = []

    # Try to extract data from sections first
    section_data = {}
    for section in sections:
        section_heading = section["heading"].lower()
        section_content = section["content"].strip()

        # Check if section heading matches any of the fields
        for field in fields:
            if field in section_heading or section_heading in field:
                section_data[field] = section_content

    # Try to extract from bullet points
    bullet_data = {}
    for bullet in bullet_points:
        # Check if bullet point contains any of the fields
        for field in fields:
            if field in bullet.lower():
                # Extract the value after the field name
                match = re.search(rf"{field}[s]?:?\s+(.*)", bullet.lower())
                if match:
                    bullet_data[field] = match.group(1)

    # Try to extract from the full content using regex patterns
    regex_data = {}
    for field in fields:
        # Common patterns for different types of data
        patterns = [
            rf"{field}[s]?:?\s+([\w\s\d.,$]+)",  # Field: Value
            rf"{field}[s]?[:\s]+([\w\s\d.,$]+)",  # Field: Value or Field Value
            rf"<{field}>(.*?)</{field}>",         # <field>Value</field>
            rf"\b{field}[s]?\b.*?(\d+[\d.,]*)"    # Field with numeric value
        ]

        for pattern in patterns:
            matches = re.findall(pattern, markdown_content.lower())
            if matches:
                regex_data[field] = matches[0].strip()
                break

    # Combine all extracted data
    combined_data = {**section_data, **bullet_data, **regex_data}

    # If we have data for at least some fields, create a row
    if combined_data:
        row = {}
        for field in fields:
            row[field] = combined_data.get(field, "")
        tabular_data.append(row)

    # If we couldn't extract structured data from sections, bullets, or general regex,
    # and fields were specified, create a fallback row.
    # This ensures that the requested fields are represented, even if mostly empty.
    if not tabular_data and fields:
        fallback_row = {field: "" for field in fields} # Initialize all requested fields to empty

        if "title" in fields: # 'fields' are already lowercased
            fallback_row["title"] = title

        # Provide a generic content snippet if 'content' or 'description' is requested
        # and not already populated by more specific regex matches (which would have put data in combined_data)
        requested_content_field = None
        if "content" in fields:
            requested_content_field = "content"
        elif "description" in fields:
            requested_content_field = "description"
        
        if requested_content_field and not combined_data.get(requested_content_field): # Check if not already found
            # Try to get a summary from the main content, avoiding just the title
            content_paragraphs = [p.strip() for p in markdown_content.split('\n\n') if p.strip()]
            if content_paragraphs:
                # Find first non-title paragraph if possible
                first_content_paragraph = ""
                for p_idx, para in enumerate(content_paragraphs):
                    if not para.startswith("#"): # Simple check to avoid title lines
                        first_content_paragraph = para
                        break
                    elif p_idx == 0 and para.lower().strip("# ").strip() == title.lower(): # If first para is title
                        continue 
                
                if not first_content_paragraph and len(content_paragraphs) > 1: # Fallback if title was complex
                    first_content_paragraph = content_paragraphs[1] if content_paragraphs[0].lower().strip("# ").strip() == title.lower() else content_paragraphs[0]

                if first_content_paragraph:
                     fallback_row[requested_content_field] = (first_content_paragraph[:250] + '...') if len(first_content_paragraph) > 250 else first_content_paragraph
                elif title != "Untitled": # If no other content, use title as a last resort for description/content
                    fallback_row[requested_content_field] = f"Content related to: {title}"
                else:
                    fallback_row[requested_content_field] = "No distinct content found."

        # Ensure only requested fields are in the fallback_row before appending
        final_fallback_row = {f: fallback_row.get(f, "") for f in fields}
        tabular_data.append(final_fallback_row)

    return tabular_data

async def extract_structured_data_with_llm(
    markdown_content: str,
    fields: List[str],
    azure_credentials: Dict[str, str]
) -> List[Dict[str, Any]]:
    """
    Extract structured data from markdown content using Azure OpenAI LLM.

    Args:
        markdown_content (str): The markdown content to process
        fields (List[str]): List of fields to extract
        azure_credentials (Dict[str, str]): Azure OpenAI credentials

    Returns:
        List[Dict[str, Any]]: Extracted data in tabular format
    """
    if not azure_credentials or 'api_key' not in azure_credentials or 'endpoint' not in azure_credentials:
        print("Error: Azure OpenAI credentials missing or incomplete")
        return []

    api_key = azure_credentials['api_key']
    endpoint = azure_credentials['endpoint']
    deployment_name = AZURE_CHAT_MODEL

    # Determine the correct API endpoint format based on the endpoint URL
    if "services.ai.azure.com" in endpoint:
        # Azure AI Studio format - use the standard Azure OpenAI format
        # Remove "/models" if it's in the endpoint
        base_endpoint = endpoint.replace("/models", "")
        url = f"{base_endpoint}/openai/deployments/{deployment_name}/chat/completions?api-version=2023-05-15"
    else:
        # Traditional Azure OpenAI format
        url = f"{endpoint}/openai/deployments/{deployment_name}/chat/completions?api-version=2023-05-15"

    # Format the prompt for the LLM
    fields_str = ", ".join(fields)
    system_prompt = f"""
    You are a data extraction assistant. Your task is to extract structured data from the provided content.
    Extract data ONLY for the following fields: {fields_str}.

    Follow these rules:
    1. CRITICAL: Extract ONLY the fields that were explicitly requested: {fields_str}. Do not add any other fields.
    2. Extract as many rows of data as you can find in the content.
    3. Each row should contain values ONLY for the specified fields. Do not add any fields that were not requested.
    4. If a field's value cannot be found for a row, use an empty string.
    5. Return the data in a valid JSON format as an array of objects, where each object represents a row.
    6. Each object should have ONLY the requested field names as keys and the extracted values as values.
    7. Do not include any explanations or notes in your response, only the JSON array.
    8. Make sure the JSON is valid and properly formatted.
    9. If the content is complex or nested, extract the most relevant data.
    10. If no data can be extracted, return an empty array [].
    11. Be precise and focused - only extract the exact fields requested, nothing more.
    12. IMPORTANT: If the user requested only one field (e.g., "price"), your response should ONLY include that field in each object, not title, description, or any other fields.
    13. NEVER add default fields like title, description, or content unless they were explicitly requested.
    14. NEVER include fields that weren't requested, even if they seem important or relevant.
    15. STRICTLY ADHERE to the requested fields list: {fields_str}. No exceptions.

    Example response format if user requested "price, brand":
    [
        {{"price": "19.99", "brand": "Nike"}},
        {{"price": "29.99", "brand": "Adidas"}},
        ...
    ]

    Example response format if user requested ONLY "price":
    [
        {{"price": "19.99"}},
        {{"price": "29.99"}},
        ...
    ]

    Remember: Only include the fields that were explicitly requested: {fields_str}. Do not add any additional fields.
    """

    user_prompt = f"Here is the content to extract data from:\n\n{markdown_content}"

    # Construct the messages
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    # Request payload
    payload = {
        "messages": messages,
        "temperature": 0.1,  # Low temperature for more deterministic output
        "top_p": 0.95,
        "max_tokens": 4000
    }

    try:
        # Make the API request
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                url,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "api-key": api_key
                }
            )

            if response.status_code != 200:
                # Consider logging this error
                return []

            # Extract the response content
            response_data = response.json()
            content = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")

            # Parse the JSON response
            try:
                # Find JSON array in the response (in case there's any extra text)
                json_start = content.find("[")
                json_end = content.rfind("]") + 1

                if json_start >= 0 and json_end > json_start:
                    json_content = content[json_start:json_end]
                    tabular_data = json.loads(json_content)

                    # Ensure the result is a list of dictionaries
                    if isinstance(tabular_data, list):
                        # Normalize field names to lowercase for consistency
                        normalized_data = []
                        for row in tabular_data:
                            if isinstance(row, dict):
                                normalized_row = {}
                                for key, value in row.items():
                                    normalized_row[key.lower()] = value
                                normalized_data.append(normalized_row)

                        return normalized_data
                    else:
                        # Consider logging this error
                        return []
                else:
                    # Consider logging this error
                    return []
            except json.JSONDecodeError as e:
                # Consider logging this error and the content
                return []
    except Exception as e:
        # Consider logging this error
        return []
