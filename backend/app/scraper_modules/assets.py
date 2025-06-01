"""
This module contains configuration variables and constants
that are used across different parts of the application.
"""

# Azure OpenAI model configuration - only models used in the application
AZURE_EMBEDDING_MODEL = "text-embedding-ada-002"
AZURE_CHAT_MODEL = "gpt-4o"

# Models configuration for Azure OpenAI only
MODELS_USED = {
    AZURE_CHAT_MODEL: {"AZURE_OPENAI_API_KEY"},
}

# Timeout settings for web scraping
TIMEOUT_SETTINGS = {
    "page_load": 30,
    "script": 10
}

NUMBER_SCROLL=2




SYSTEM_MESSAGE = """You are an intelligent text extraction and conversion assistant. Your task is to extract structured information
                        from the given text and convert it into a pure JSON format. The JSON should contain only the structured data extracted from the text,
                        with no additional commentary, explanations, or extraneous information.
                        You could encounter cases where you can't find the data of the fields you have to extract or the data will be in a foreign language.
                        Please process the following text and provide the output in pure JSON format with no words before or after the JSON:"""

def generate_user_focused_system_message(fields: list) -> str:
    """Generate a system message that prioritizes user-specified fields"""
    fields_str = ", ".join(fields)

    return f"""You are an intelligent text extraction and conversion assistant. Your PRIMARY task is to extract ONLY the specific fields requested by the user.

USER REQUESTED FIELDS: {fields_str}

CRITICAL INSTRUCTIONS:
1. ONLY extract data for these exact fields: {fields_str}
2. Do NOT add any additional fields that you think might be useful
3. Do NOT rename fields - use the exact field names provided by the user
4. If a requested field cannot be found, include it with an empty string value
5. Focus on finding data that matches the user's field names, even if the website uses different terminology

For example:
- If user requests "name" and the website shows "country", map "country" data to the "name" field
- If user requests "price" and the website shows "cost", map "cost" data to the "price" field
- If user requests "area" and the website shows "size" or "area (km2)", map that data to the "area" field

Your output must be a pure JSON format with no additional commentary, explanations, or extraneous information.
You could encounter cases where you can't find the data of the fields you have to extract or the data will be in a foreign language.
Please process the following text and provide the output in pure JSON format with no words before or after the JSON:"""

USER_MESSAGE = f"Extract the following information from the provided text:\nPage content:\n\n"
        




PROMPT_PAGINATION = """
You are an assistant that extracts pagination URLs from markdown content of websites. 
Your task is to identify and generate a list of pagination URLs based on a detected URL pattern where page numbers increment sequentially. Follow these instructions carefully:

-Identify the Pagination Pattern:
Analyze the provided markdown text to detect URLs that follow a pattern where only a numeric page indicator changes.
If the numbers start from a low value and increment, generate the full sequence of URLs—even if not all numbers are present in the text.

-Construct Complete URLs:
In cases where only part of a URL is provided, combine it with the given base URL (which will appear at the end of this prompt) to form complete URLs.
Ensure that every URL you generate is clickable and leads directly to the intended page.

-Incorporate User Indications:
If additional user instructions about the pagination mechanism are provided at the end of the prompt, use those instructions to refine your URL generation.
Output Format Requirements:

-Strictly output only a valid JSON object with the exact structure below:
""
{
    "page_urls": ["url1", "url2", "url3", ..., "urlN"]
}""


IMPORTANT:

Output only a single valid JSON object with no additional text, markdown formatting, or explanation.
Do not include any extra newlines or spaces before or after the JSON.
The JSON object must exactly match the following schema:
"""
