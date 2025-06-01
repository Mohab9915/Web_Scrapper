import asyncio
import os
import json # Import the json module
from backend.app.scraper_modules.scraper import scrape_urls
from backend.app.scraper_modules.markdown import save_raw_data, read_raw_data # Assuming read_raw_data is needed if scrape_urls uses it internally
from backend.app.scraper_modules.utils import generate_unique_name
from backend.app.scraper_modules.assets import AZURE_CHAT_MODEL # Use Azure OpenAI model
from backend.app.database import supabase # To ensure DB is accessible for save/read if needed by scrape_urls's dependencies

# Ensure API keys are set in your environment for the chosen model, e.g., OPENAI_API_KEY
# For testing, you might need to set them directly if not using a .env file loaded by the main app
# Example: os.environ["OPENAI_API_KEY"] = "your_key_here" 
# However, the app's get_api_key logic should handle this if keys are in the usual places (e.g. project settings table or .env)

async def main():
    print("Starting real URL markdown to structured data test...")

    # 1. Define the real URL
    real_url = "https://webscraper.io/test-sites/e-commerce/allinone"
    print(f"Target URL: {real_url}\n")

    # 2. Define fields to extract
    target_fields = ["name", "price"]
    print(f"Target Fields: {target_fields}\n")

    # 3. Fetch and store markdown for the real URL
    # This will also generate and return the unique_name
    unique_name = None
    try:
        print(f"Fetching and storing markdown for {real_url}...")
        # fetch_and_store_markdowns is async
        from backend.app.scraper_modules.markdown import fetch_and_store_markdowns
        unique_names_list = await fetch_and_store_markdowns([real_url])
        if not unique_names_list:
            print("Failed to get unique_name from fetch_and_store_markdowns.")
            return
        unique_name = unique_names_list[0]
        print(f"Markdown fetched and stored. Unique Name: {unique_name}\n")
        
        # Optionally, verify markdown content
        # fetched_markdown = read_raw_data(unique_name)
        # print(f"Fetched Markdown (first 200 chars):\n{fetched_markdown[:200]}...\n")

    except Exception as e:
        print(f"Error fetching/storing markdown for {real_url}: {e}")
        import traceback
        traceback.print_exc()
        return

    # 4. Call scrape_urls
    # Select a model. Ensure its API key is available.
    selected_model = AZURE_CHAT_MODEL
    print(f"Calling scrape_urls for unique_name '{unique_name}' with model: {selected_model}...\n")

    try:
        total_input_tokens, total_output_tokens, total_cost, parsed_results = scrape_urls(
            unique_names=[unique_name], 
            fields=target_fields, 
            selected_model=selected_model
        )

        print("\n--- scrape_urls Results ---")
        print(f"Total Input Tokens: {total_input_tokens}")
        print(f"Total Output Tokens: {total_output_tokens}")
        print(f"Total Cost: ${total_cost:.6f}")
        
        if parsed_results:
            print("\nParsed Data (from scrape_urls):")
            for result in parsed_results:
                print(f"  Unique Name: {result['unique_name']}")
                # The 'parsed_data' should be an instance of DynamicListingsContainer (or its dict form)
                # which means it should have a 'listings' key.
                parsed_data_content = result['parsed_data']
                if hasattr(parsed_data_content, 'model_dump_json'): # If it's a Pydantic model
                    print(f"  Parsed Content (JSON): {parsed_data_content.model_dump_json(indent=2)}")
                elif isinstance(parsed_data_content, dict): # If it's already a dict
                    print(f"  Parsed Content (Dict): {json.dumps(parsed_data_content, indent=2)}")
                else: # If it's a string or something else
                    print(f"  Parsed Content (Raw): {parsed_data_content}")

                # Specifically check for the 'listings' key if it's a dict
                if isinstance(parsed_data_content, dict) and 'listings' in parsed_data_content:
                    print(f"\n  Extracted Listings (should be a list of items with name, price, description):")
                    for item in parsed_data_content['listings']:
                        print(f"    - {item}")
                elif hasattr(parsed_data_content, 'listings'): # Pydantic model access
                     print(f"\n  Extracted Listings (should be a list of items with name, price, description):")
                     for item in parsed_data_content.listings:
                        print(f"    - {item.model_dump() if hasattr(item, 'model_dump') else item}")

        else:
            print("No parsed results returned from scrape_urls.")

    except Exception as e:
        print(f"An error occurred during scrape_urls call: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # If running this script directly, ensure any necessary async setup is handled.
    # For simplicity, if main functions in scraper_modules are sync, this is fine.
    # If they become async, this runner would need to be async too.
    # Current scrape_urls is synchronous.
    asyncio.run(main())
