# scraper.py

import json
from typing import List
from pydantic import BaseModel, create_model
from .assets import (AZURE_CHAT_MODEL,SYSTEM_MESSAGE,generate_user_focused_system_message)
from .llm_calls import (call_llm_model)
from .markdown import read_raw_data
# from .api_management import get_supabase_client # No longer needed for supabase client here
from ..database import supabase # Use the app's global supabase client
from .utils import  generate_unique_name

# supabase = get_supabase_client() # Removed: Use imported supabase client

def create_dynamic_listing_model(field_names: List[str]):
    field_definitions = {field: (str, ...) for field in field_names}
    return create_model('DynamicListingModel', **field_definitions)

def create_listings_container_model(listing_model: BaseModel):
    return create_model('DynamicListingsContainer', listings=(List[listing_model], ...))

def generate_system_message(listing_model: BaseModel, fields: List[str] = None) -> str:
    # Get schema info
    schema_info = listing_model.model_json_schema()
    field_descriptions = []
    for field_name, field_info in schema_info["properties"].items():
        field_type = field_info["type"]
        field_descriptions.append(f'"{field_name}": "{field_type}"')

    schema_structure = ",\n".join(field_descriptions)

    # Use user-focused system message if fields are provided
    if fields:
        base_message = generate_user_focused_system_message(fields)
    else:
        base_message = SYSTEM_MESSAGE

    final_prompt = base_message + "\n" + f"""strictly follows this schema:
    {{
       "listings": [
         {{
           {schema_structure}
         }}
       ]
    }}
    """

    return final_prompt


def save_formatted_data(unique_name: str, formatted_data):
    if isinstance(formatted_data, str):
        try:
            data_json = json.loads(formatted_data)
        except json.JSONDecodeError:
            data_json = {"raw_text": formatted_data}
    elif hasattr(formatted_data, "dict"):
        data_json = formatted_data.dict()
    else:
        data_json = formatted_data

    # Update the scrape session with formatted data
    # The unique_name is a timestamp-based name, not project_id_session_id format
    # We need to find the session by unique_scrape_identifier
    try:
        # Use unique_scrape_identifier to find and update the session
        supabase.table("scrape_sessions").update({
            "formatted_tabular_data": data_json
        }).eq("unique_scrape_identifier", unique_name).execute()
    except Exception as e:
        print(f"Warning: Could not update scrape session with formatted data: {e}")
        # Continue without failing the scraping process
    MAGENTA = "\033[35m"
    RESET = "\033[0m"  # Reset color to default
    print(f"{MAGENTA}INFO:Scraped data saved for {unique_name}{RESET}")

def scrape_urls(unique_names: List[str], fields: List[str], selected_model: str):
    """
    For each unique_name:
      1) read raw_data from supabase
      2) parse with selected LLM
      3) save formatted_data
      4) accumulate cost
    Return total usage + list of final parsed data
    """
    total_input_tokens = 0
    total_output_tokens = 0
    total_cost = 0
    parsed_results = []

    DynamicListingModel = create_dynamic_listing_model(fields)
    DynamicListingsContainer = create_listings_container_model(DynamicListingModel)

    for uniq in unique_names:
        raw_data = read_raw_data(uniq)
        if not raw_data:
            BLUE = "\033[34m"
            RESET = "\033[0m"
            print(f"{BLUE}No raw_data found for {uniq}, skipping.{RESET}")
            continue

        # Generate the specific system message that includes the schema for DynamicListingModel within the "listings" structure
        # Pass the fields to prioritize user-specified conditions
        specific_system_message = generate_system_message(DynamicListingModel, fields)
        parsed, token_counts, cost = call_llm_model(raw_data, DynamicListingsContainer, selected_model, specific_system_message)

        current_result_entry = {
            "unique_name": uniq,
            "parsed_data": None,
            "save_error": None,
            "llm_error": None
        }

        if parsed is not None:
            current_result_entry["parsed_data"] = parsed  # Store the actual LLM output
            try:
                save_formatted_data(uniq, parsed)
            except Exception as e:
                print(f"Error saving formatted data for {uniq}: {e}")
                current_result_entry["save_error"] = f"Failed to save formatted data: {str(e)}"
        else:
            print(f"Warning: LLM call for {uniq} returned None or failed parsing. Skipping save_formatted_data.")
            current_result_entry["llm_error"] = "LLM returned None or failed to parse"
            # Keep current_result_entry["parsed_data"] as None, or set to an error dict
            current_result_entry["parsed_data"] = {"error": "LLM returned None or failed to parse"} # Match previous behavior for this field on LLM error

        # Ensure token_counts and cost are valid
        if token_counts:
            total_input_tokens += token_counts.get("input_tokens", 0)
            total_output_tokens += token_counts.get("output_tokens", 0)
        if cost is not None:
            total_cost += cost
            
        parsed_results.append(current_result_entry)

    return total_input_tokens, total_output_tokens, total_cost, parsed_results
