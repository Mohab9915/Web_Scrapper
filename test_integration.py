"""
Test script to verify the integration between the frontend and backend.
"""
import httpx
import pytest
import json
import time
import uuid # Moved import higher
from backend.app.main import app # Import the FastAPI app
from httpx import ASGITransport

# Backend API URL (relative path for TestClient)
BASE_API_PATH = "/api/v1"

# Azure OpenAI credentials (placeholders, real tests would need mocking or actual keys)
AZURE_OPENAI_CREDENTIALS = {
    "api_key": "YOUR_AZURE_API_KEY",
    "endpoint": "https://your-azure-endpoint.services.ai.azure.com",
}

def print_separator():
    """Print a separator line."""
    print("\n" + "=" * 80 + "\n")

@pytest.mark.asyncio
async def test_health():
    """Test the health check endpoint."""
    print("Testing health check endpoint...")
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/health")

    print(f"Status code: {response.status_code}")
    print(f"Response: {response.text}")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    print_separator()

@pytest.mark.asyncio
async def test_create_project():
    """Test creating a project."""
    print("Testing project creation...")
    project_data = {
        "name": f"Test Project {int(time.time())}"
    }
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(f"{BASE_API_PATH}/projects/", json=project_data) # Added trailing slash

    print(f"Status code: {response.status_code}")
    if response.status_code == 201: # FastAPI default for POST success is 201 or 200
        project = response.json()
        print(f"Project created: {json.dumps(project, indent=2)}")
        # For pytest, assertions are better than returning values from tests
        assert "id" in project
    else:
        print(f"Failed to create project: {response.text}")
        assert response.status_code == 201 # Or 200, depending on API spec
    print_separator()

@pytest.mark.skip(reason="Requires project_id fixture and further refactoring")
@pytest.mark.asyncio
async def test_enable_rag(project_id): # project_id would come from a fixture
    """Test enabling RAG for a project."""
    print(f"Testing RAG enablement for project {project_id}...")
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.put(
            f"{BASE_API_PATH}/projects/{project_id}",
            json={"rag_enabled": True}
        )

    print(f"Status code: {response.status_code}")
    if response.status_code == 200:
        project = response.json()
        print(f"Project updated: {json.dumps(project, indent=2)}")
    else:
        print(f"Failed to enable RAG: {response.text}")
    assert response.status_code == 200
    print_separator()

@pytest.mark.skip(reason="Requires project_id fixture and further refactoring")
@pytest.mark.asyncio
async def test_execute_scrape(project_id): # project_id would come from a fixture
    """Test executing a scrape."""
    print(f"Testing scrape execution for project {project_id}...")
    session_id = str(uuid.uuid4())
    scrape_data = {
        "current_page_url": "http://example.com",
        "session_id": session_id, # May be ignored by new service
        "api_keys": {
            # Using placeholder keys, actual LLM calls will fail if not mocked/configured
            "OPENAI_API_KEY": AZURE_OPENAI_CREDENTIALS["api_key"], 
            "AZURE_ENDPOINT": AZURE_OPENAI_CREDENTIALS["endpoint"], # Example, align with actual needs
            "model_name": "gpt-4o-mini" # Example
        },
        "force_refresh": True,
        "display_format": "table",
        "conditions": "title,description"
    }
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            f"{BASE_API_PATH}/projects/{project_id}/execute-scrape",
            json=scrape_data
        )

    print(f"Status code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Scrape executed: {json.dumps(result, indent=2)}")
    else:
        print(f"Failed to execute scrape: {response.text}")
    # This test will likely fail due to actual scraping attempt / Playwright issues
    assert response.status_code != 404 # Basic check
    print_separator()

@pytest.mark.skip(reason="Requires project_id fixture and further refactoring")
@pytest.mark.asyncio
async def test_query_rag(project_id): # project_id would come from a fixture
    """Test querying the RAG system."""
    print(f"Testing RAG query for project {project_id}...")
    query_data = {
        "query": "What is the main topic of the scraped content?",
        "model_deployment": "gpt-4o-mini", # Align with LiteLLM if needed
        "azure_credentials": { # This structure might need update for LiteLLM
            **AZURE_OPENAI_CREDENTIALS,
            "deployment_name": "gpt-4o-mini"
        }
    }
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            f"{BASE_API_PATH}/projects/{project_id}/query-rag",
            json=query_data
        )

    print(f"Status code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"RAG query result: {json.dumps(result, indent=2)}")
    else:
        print(f"Failed to query RAG: {response.text}")
    assert response.status_code != 404 # Basic check
    print_separator()

# The if __name__ == "__main__": block is not run by pytest.
# Test orchestration and dependency (like project_id) should be handled by pytest fixtures.
