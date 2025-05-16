"""
Test script to test the API endpoints.
"""
import requests
import json
import uuid

# Backend API URL
API_URL = "http://localhost:8001/api/v1"

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

def test_get_projects():
    """Test getting all projects."""
    print("Testing GET /projects endpoint...")
    
    response = requests.get(f"{API_URL}/projects")
    
    print(f"Status code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2) if response.status_code == 200 else response.text}")
    
    print_separator()
    
    return response.json()[0]["id"] if response.status_code == 200 and response.json() else None

def test_enable_rag(project_id):
    """Test enabling RAG for a project."""
    print(f"Testing PUT /projects/{project_id} endpoint to enable RAG...")
    
    response = requests.put(
        f"{API_URL}/projects/{project_id}",
        json={"rag_enabled": True}
    )
    
    print(f"Status code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2) if response.status_code == 200 else response.text}")
    
    print_separator()

def test_execute_scrape(project_id):
    """Test executing a scrape."""
    print(f"Testing POST /projects/{project_id}/execute-scrape endpoint...")
    
    # Generate a session ID
    session_id = str(uuid.uuid4())
    
    # Create the request payload
    payload = {
        "current_page_url": "http://example.com",
        "session_id": session_id,
        "api_keys": {
            "api_key": "test-api-key",
            "endpoint": "https://test-endpoint.openai.azure.com"
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

def test_query_rag(project_id):
    """Test querying the RAG system."""
    print(f"Testing POST /projects/{project_id}/query-rag endpoint...")
    
    # Create the request payload
    payload = {
        "query": "What is the main topic of the scraped content?",
        "model_deployment": "gpt-35-turbo",
        "azure_credentials": {
            "api_key": "test-api-key",
            "endpoint": "https://test-endpoint.openai.azure.com"
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
    test_health()
    project_id = test_get_projects()
    
    if project_id:
        print(f"Using project ID: {project_id}")
        test_enable_rag(project_id)
        test_execute_scrape(project_id)
        test_query_rag(project_id)
    else:
        print("No projects found. Please create a project first.")
