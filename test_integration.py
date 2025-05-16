"""
Test script to verify the integration between the frontend and backend.
"""
import requests
import json
import time

# Backend API URL
API_URL = "http://localhost:8001/api/v1"

# Azure OpenAI credentials
AZURE_OPENAI_CREDENTIALS = {
    "api_key": "BuVHZw4d7OmEwH5QIsvw8gsKLyRxNUow4PT1gYg83iukV6JLRVL8JQQJ99BDACHYHv6XJ3w3AAAAACOGR8LC",
    "endpoint": "https://practicehub3994533910.services.ai.azure.com",
}

def print_separator():
    """Print a separator line."""
    print("\n" + "=" * 80 + "\n")

def test_health():
    """Test the health check endpoint."""
    print("Testing health check endpoint...")

    response = requests.get("http://localhost:8001/health")

    print(f"Status code: {response.status_code}")
    print(f"Response: {response.text}")

    print_separator()
    return response.status_code == 200

def test_create_project():
    """Test creating a project."""
    print("Testing project creation...")

    project_data = {
        "name": f"Test Project {int(time.time())}"
    }

    response = requests.post(
        f"{API_URL}/projects",
        json=project_data
    )

    print(f"Status code: {response.status_code}")
    if response.status_code == 201:
        project = response.json()
        print(f"Project created: {json.dumps(project, indent=2)}")
        return project
    else:
        print(f"Failed to create project: {response.text}")
        return None

def test_enable_rag(project_id):
    """Test enabling RAG for a project."""
    print(f"Testing RAG enablement for project {project_id}...")

    response = requests.put(
        f"{API_URL}/projects/{project_id}",
        json={"rag_enabled": True}
    )

    print(f"Status code: {response.status_code}")
    if response.status_code == 200:
        project = response.json()
        print(f"Project updated: {json.dumps(project, indent=2)}")
        return project
    else:
        print(f"Failed to enable RAG: {response.text}")
        return None

def test_execute_scrape(project_id):
    """Test executing a scrape."""
    print(f"Testing scrape execution for project {project_id}...")

    import uuid
    session_id = str(uuid.uuid4())

    scrape_data = {
        "current_page_url": "http://example.com",
        "session_id": session_id,
        "api_keys": {
            **AZURE_OPENAI_CREDENTIALS,
            "deployment_name": "text-embedding-ada-002"
        }
    }

    response = requests.post(
        f"{API_URL}/projects/{project_id}/execute-scrape",
        json=scrape_data
    )

    print(f"Status code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Scrape executed: {json.dumps(result, indent=2)}")
        return session_id
    else:
        print(f"Failed to execute scrape: {response.text}")
        return None

def test_query_rag(project_id):
    """Test querying the RAG system."""
    print(f"Testing RAG query for project {project_id}...")

    query_data = {
        "query": "What is the main topic of the scraped content?",
        "model_deployment": "gpt-4o-mini",
        "azure_credentials": {
            **AZURE_OPENAI_CREDENTIALS,
            "deployment_name": "gpt-4o-mini"
        }
    }

    response = requests.post(
        f"{API_URL}/projects/{project_id}/query-rag",
        json=query_data
    )

    print(f"Status code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"RAG query result: {json.dumps(result, indent=2)}")
        return result
    else:
        print(f"Failed to query RAG: {response.text}")
        return None

def main():
    """Run the integration tests."""
    if not test_health():
        print("Health check failed. Exiting.")
        return

    project = test_create_project()
    if not project:
        print("Project creation failed. Exiting.")
        return

    project_id = project["id"]

    updated_project = test_enable_rag(project_id)
    if not updated_project:
        print("RAG enablement failed. Exiting.")
        return

    # Wait for RAG to be enabled
    print("Waiting for RAG to be enabled...")
    time.sleep(2)

    session_id = test_execute_scrape(project_id)
    if not session_id:
        print("Scrape execution failed. Exiting.")
        return

    # Wait for scrape to be processed
    print("Waiting for scrape to be processed...")
    time.sleep(5)

    rag_result = test_query_rag(project_id)
    if not rag_result:
        print("RAG query failed. Exiting.")
        return

    print("\nAll integration tests passed successfully!")

if __name__ == "__main__":
    main()
