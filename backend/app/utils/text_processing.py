"""
Utility functions for text processing.
"""
import re
import json
import httpx
from typing import List, Dict, Any, Optional
import tiktoken

from app.utils.crawl4ai_crawler import AZURE_CHAT_MODEL

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
    display_format: str
) -> Dict[str, Any]:
    """
    Format tabular data for display based on the specified format.

    Args:
        tabular_data (List[Dict[str, Any]]): Tabular data to format
        fields (List[str]): List of fields in the data
        display_format (str): Display format ('table', 'paragraph', or 'raw')

    Returns:
        Dict[str, Any]: Formatted data
    """
    if not tabular_data:
        return {
            "table_data": [],
            "paragraph_data": "",
            "raw_data": ""
        }

    # Format data for table view (already in the right format)
    table_data = tabular_data

    # Format data for paragraph view
    paragraph_data = ""
    for i, row in enumerate(tabular_data):
        paragraph_data += f"Item {i+1}:\n"
        for field in fields:
            if field in row and row[field]:
                paragraph_data += f"{field.capitalize()}: {row[field]}\n"
        paragraph_data += "\n"

    # Format data for raw view
    raw_data = ""
    for i, row in enumerate(tabular_data):
        raw_data += f"--- Item {i+1} ---\n"
        for field, value in row.items():
            if value:
                raw_data += f"{field}: {value}\n"
        raw_data += "\n"

    return {
        "table_data": table_data,
        "paragraph_data": paragraph_data,
        "raw_data": raw_data
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

    # If we couldn't extract structured data, create a simple table with ONLY the requested fields
    if not tabular_data:
        # Create a fallback row with ONLY the requested fields
        row = {}
        for field in fields:
            # Only add fields that were explicitly requested
            if field == "title" and "title" in fields:
                row[field] = title
            elif (field == "content" or field == "description") and field in fields:
                # Get the first paragraph of content
                paragraphs = [p for p in markdown_content.split('\n\n') if p.strip()]
                if paragraphs and len(paragraphs) > 1:
                    row[field] = paragraphs[1].strip()  # Skip the title paragraph
            else:
                # Only add the field if it was explicitly requested
                if field in fields:
                    row[field] = ""

        # Only add the row if it has at least one non-empty value, contains ONLY the requested fields,
        # and the extracted values are meaningful (not just empty strings or generic content)
        meaningful_values = [v for v in row.values() if v and v.strip() and len(v.strip()) > 3]
        if (len(meaningful_values) >= len(fields) * 0.5 and  # At least 50% of fields have meaningful values
            all(field in fields for field in row.keys()) and
            any(value for value in row.values())):
            tabular_data.append(row)

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
                print(f"Error from Azure OpenAI API: {response.status_code} - {response.text}")
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
                        print("Error: LLM response is not a list")
                        return []
                else:
                    print("Error: Could not find JSON array in LLM response")
                    return []
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON from LLM response: {e}")
                print(f"Response content: {content}")
                return []
    except Exception as e:
        print(f"Error calling Azure OpenAI API: {e}")
        return []
