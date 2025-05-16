"""
Test script to test the RAG functionality with real Azure OpenAI credentials.
"""
import requests
import json
import uuid

# Backend API URL
API_URL = "http://localhost:8001/api/v1"

# Azure AI Studio configuration
AZURE_OPENAI_CONFIG = {
    "api_key": "BuVHZw4d7OmEwH5QIsvw8gsKLyRxNUow4PT1gYg83iukV6JLRVL8JQQJ99BDACHYHv6XJ3w3AAAAACOGR8LC",
    "endpoint": "https://practicehub3994533910.services.ai.azure.com/models",
    "chat_deployment_name": "gpt-4o-mini",
    "embedding_deployment_name": "text-embedding-ada-002"
}

def print_separator():
    """Print a separator line."""
    print("\n" + "=" * 80 + "\n")

def get_project_id():
    """Get the project ID."""
    response = requests.get(f"{API_URL}/projects")
    if response.status_code == 200:
        projects = response.json()
        if projects:
            return projects[0]["id"]
    return None

def execute_scrape(project_id):
    """Execute a scrape with real Azure OpenAI credentials."""
    print(f"Executing scrape for project {project_id} with real Azure OpenAI credentials...")

    # Generate a session ID
    session_id = str(uuid.uuid4())

    # Create the request payload
    payload = {
        "current_page_url": "http://example.com",
        "session_id": session_id,
        "api_keys": {
            "api_key": AZURE_OPENAI_CONFIG["api_key"],
            "endpoint": AZURE_OPENAI_CONFIG["endpoint"],
            "deployment_name": AZURE_OPENAI_CONFIG["embedding_deployment_name"]
        }
    }

    print(f"Request payload: {json.dumps(payload, indent=2)}")

    response = requests.post(
        f"{API_URL}/projects/{project_id}/execute-scrape",
        json=payload
    )

    print(f"Status code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2) if response.status_code == 200 else response.text}")

    print_separator()

    return session_id if response.status_code == 200 else None

def wait_for_rag_ingestion(project_id, session_id):
    """Wait for RAG ingestion to complete."""
    print(f"Waiting for RAG ingestion to complete for session {session_id}...")

    max_attempts = 10
    for attempt in range(max_attempts):
        response = requests.get(f"{API_URL}/projects/{project_id}/sessions")

        if response.status_code == 200:
            sessions = response.json()
            for session in sessions:
                if session["id"] == session_id:
                    print(f"Session status: {session['status']}")
                    if session["status"] == "rag_ingested":
                        print("RAG ingestion completed successfully!")
                        print_separator()
                        return True

        print(f"Attempt {attempt + 1}/{max_attempts}: RAG ingestion still in progress...")
        import time
        time.sleep(2)  # Wait for 2 seconds before checking again

    print("RAG ingestion did not complete within the expected time.")
    print_separator()
    return False

def query_rag(project_id):
    """Query the RAG system with real Azure OpenAI credentials."""
    print(f"Querying RAG for project {project_id} with real Azure OpenAI credentials...")

    # Create the request payload
    payload = {
        "query": "What is the main topic of the scraped content?",
        "model_deployment": AZURE_OPENAI_CONFIG["chat_deployment_name"],
        "azure_credentials": {
            "api_key": AZURE_OPENAI_CONFIG["api_key"],
            "endpoint": AZURE_OPENAI_CONFIG["endpoint"],
            "deployment_name": AZURE_OPENAI_CONFIG["chat_deployment_name"]
        }
    }

    print(f"Request payload: {json.dumps(payload, indent=2)}")

    response = requests.post(
        f"{API_URL}/projects/{project_id}/query-rag",
        json=payload
    )

    print(f"Status code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2) if response.status_code == 200 else response.text}")

    print_separator()

if __name__ == "__main__":
    project_id = get_project_id()

    if project_id:
        print(f"Using project ID: {project_id}")
        session_id = execute_scrape(project_id)

        if session_id:
            if wait_for_rag_ingestion(project_id, session_id):
                query_rag(project_id)
        else:
            print("Scrape execution failed. Skipping RAG query.")
    else:
        print("No projects found. Please create a project first.")
