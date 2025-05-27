#!/usr/bin/env python3
"""
Test script for RAG system improvements.
"""
import argparse
import asyncio
import json
import sys
import time
import uuid
from datetime import datetime
import requests
import websockets
import pytest # Added for pytest markers

# Azure OpenAI credentials
AZURE_OPENAI_CREDENTIALS = {
    "api_key": "YOUR_AZURE_API_KEY",
    "endpoint": "https://your-azure-endpoint.services.ai.azure.com"
}

# Azure OpenAI model configuration
AZURE_EMBEDDING_MODEL = "text-embedding-ada-002"
AZURE_CHAT_MODEL = "gpt-4o-mini"

# Backend API URL
API_URL = "http://localhost:8001/api/v1" # Standardized port
WS_URL = "ws://localhost:8001/api/v1"  # Standardized port

def log_message(message, level="INFO", verbose=False):
    """Log a message with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if level == "INFO" or verbose:
        print(f"[{timestamp}] {level}: {message}")

def handle_error(message, error=None, exit_script=True):
    """Handle errors and exit gracefully if needed."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] ERROR: {message}")
    if error:
        print(f"Details: {error}")
    if exit_script:
        print("Exiting...")
        sys.exit(1)

@pytest.mark.skip(reason="Requires project_id and session_id fixtures")
async def test_websocket_progress(project_id, session_id, verbose=False): # Already async
    """Test WebSocket progress updates."""
    log_message(f"Connecting to WebSocket for project {project_id}...", verbose=verbose)

    try:
        async with websockets.connect(f"{WS_URL}/ws/projects/{project_id}") as websocket:
            log_message("WebSocket connection established", verbose=verbose)

            # Wait for progress updates
            while True:
                try:
                    message = await websocket.recv()
                    data = json.loads(message)

                    if data.get("type") == "progress_update" and data.get("session_id") == session_id:
                        progress_data = data.get("data", {})
                        status = progress_data.get("status")
                        message = progress_data.get("message")
                        current = progress_data.get("current_chunk", 0)
                        total = progress_data.get("total_chunks", 0)
                        percent = progress_data.get("percent_complete", 0)

                        log_message(f"Progress: {status} - {message} ({current}/{total}, {percent}%)")

                        # If processing is completed or errored, break the loop
                        if status in ["completed", "error"]:
                            log_message(f"Processing {status}: {message}")
                            break
                except Exception as e:
                    log_message(f"Error receiving WebSocket message: {e}", level="ERROR")
                    break
    except Exception as e:
        handle_error(f"WebSocket connection error: {e}", exit_script=False)

def create_project(api_url, verbose=False):
    """Create a new project."""
    log_message("Creating a new project...", verbose=verbose)

    try:
        response = requests.post(
            f"{api_url}/projects",
            json={"name": f"RAG Improvements Test {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"}
        )
        response.raise_for_status()
        project = response.json()
        log_message(f"Project created with ID: {project['id']}", verbose=verbose)
        return project
    except Exception as e:
        handle_error("Failed to create project", e)

def enable_rag(api_url, project_id, verbose=False):
    """Enable RAG for a project."""
    log_message(f"Enabling RAG for project {project_id}...", verbose=verbose)

    try:
        # Use the correct endpoint for enabling RAG
        response = requests.put(
            f"{api_url}/projects/{project_id}",
            json={"rag_enabled": True}
        )
        response.raise_for_status()
        project = response.json()
        log_message(f"RAG status: {project['rag_status']}", verbose=verbose)
        return project
    except Exception as e:
        handle_error("Failed to enable RAG", e)

def execute_scrape(api_url, project_id, url="https://en.wikipedia.org/wiki/Retrieval-augmented_generation", verbose=False):
    """Execute a scrape operation."""
    log_message(f"Executing scrape for project {project_id} on URL: {url}...", verbose=verbose)

    session_id = str(uuid.uuid4())

    try:
        # Create API keys with specific embedding deployment name
        api_keys = {
            **AZURE_OPENAI_CREDENTIALS,
            "deployment_name": AZURE_EMBEDDING_MODEL
        }

        response = requests.post(
            f"{api_url}/projects/{project_id}/execute-scrape",
            json={
                "current_page_url": url,
                "session_id": session_id,
                "api_keys": api_keys
            }
        )
        response.raise_for_status()
        session = response.json()

        # Print the full response for debugging
        if verbose:
            log_message(f"Full response: {json.dumps(session, indent=2)}")

        # Check if the response has the expected structure
        if isinstance(session, dict) and 'id' in session:
            log_message(f"Scrape executed with session ID: {session['id']}", verbose=verbose)
        else:
            # Try to extract session ID from the response if it has a different structure
            session_id = session.get('session_id') or session_id
            log_message(f"Scrape executed with session ID: {session_id}", verbose=verbose)
            session = {'id': session_id}

        return session
    except Exception as e:
        handle_error("Failed to execute scrape", e)

def get_cache_stats(api_url, verbose=False):
    """Get cache statistics."""
    log_message("Getting cache statistics...", verbose=verbose)

    try:
        response = requests.get(f"{api_url}/cache/stats")
        response.raise_for_status()
        stats = response.json()
        log_message(f"Cache stats: {json.dumps(stats, indent=2)}", verbose=verbose)
        return stats
    except Exception as e:
        handle_error("Failed to get cache statistics", e, exit_script=False)
        return None

@pytest.mark.skip(reason="Requires api_url, project_id, and url fixtures, and uses direct requests")
def test_cached_scrape(api_url, project_id, url, verbose=False):
    """Test cached scrape by executing the same URL twice."""
    log_message(f"Testing cached scrape for URL: {url}...", verbose=verbose)

    # First scrape - should miss cache
    start_time = time.time()
    session1 = execute_scrape(api_url, project_id, url, verbose)
    first_scrape_time = time.time() - start_time
    log_message(f"First scrape took {first_scrape_time:.2f} seconds", verbose=verbose)

    # Get cache stats after first scrape
    stats1 = get_cache_stats(api_url, verbose)

    # Second scrape - should hit cache
    start_time = time.time()
    session2 = execute_scrape(api_url, project_id, url, verbose)
    second_scrape_time = time.time() - start_time
    log_message(f"Second scrape took {second_scrape_time:.2f} seconds", verbose=verbose)

    # Get cache stats after second scrape
    stats2 = get_cache_stats(api_url, verbose)

    # Calculate improvement
    if first_scrape_time > 0:
        improvement = (first_scrape_time - second_scrape_time) / first_scrape_time * 100
        log_message(f"Cache improved performance by {improvement:.2f}%", verbose=verbose)

    return {
        "first_scrape_time": first_scrape_time,
        "second_scrape_time": second_scrape_time,
        "cache_stats_before": stats1,
        "cache_stats_after": stats2
    }

async def main():
    parser = argparse.ArgumentParser(description="Test RAG system improvements")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("--url", default="https://en.wikipedia.org/wiki/Retrieval-augmented_generation",
                        help="URL to scrape (default: Wikipedia RAG page)")
    parser.add_argument("--api-url", default=API_URL, help=f"Backend API URL (default: {API_URL})")
    parser.add_argument("--test-cache", action="store_true", help="Test caching by scraping the same URL twice")
    parser.add_argument("--test-websocket", action="store_true", help="Test WebSocket progress updates")
    args = parser.parse_args()

    # Create a new project
    project = create_project(args.api_url, args.verbose)

    # Enable RAG for the project
    project = enable_rag(args.api_url, project["id"], args.verbose)

    # Execute scrape
    session = execute_scrape(args.api_url, project["id"], args.url, args.verbose)

    # Test WebSocket progress updates if requested
    if args.test_websocket:
        await test_websocket_progress(project["id"], session["id"], args.verbose)

    # Test caching if requested
    if args.test_cache:
        cache_results = test_cached_scrape(args.api_url, project["id"], args.url, args.verbose)
        log_message(f"Cache test results: {json.dumps(cache_results, indent=2)}")

    log_message("All tests completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
