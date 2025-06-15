"""
Script to run the application.
"""
import os
import uvicorn
from dotenv import load_dotenv

# Explicitly load environment variables from .env file
load_dotenv()

# Verify Azure OpenAI credentials are loaded
api_key = os.getenv("AZURE_OPENAI_API_KEY")
endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
api_version = os.getenv("AZURE_OPENAI_API_VERSION")

if not api_key or not endpoint:
    print("WARNING: Azure OpenAI credentials not found in environment variables!")
    print(f"AZURE_OPENAI_API_KEY present: {bool(api_key)}")
    print(f"AZURE_OPENAI_ENDPOINT present: {bool(endpoint)}")
    print(f"AZURE_OPENAI_API_VERSION: {api_version}")
    print("RAG functionality may not work correctly.")
else:
    print("✅ Azure OpenAI credentials loaded successfully.")

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
