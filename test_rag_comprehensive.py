#!/usr/bin/env python3
"""
Test script for RAG (Retrieval-Augmented Generation) functionality.

This script tests the RAG functionality of the system by:
1. Creating a new project
2. Enabling RAG for the project
3. Executing a scrape operation on a sample URL
4. Waiting for the scrape to be processed
5. Querying the RAG system with a relevant question
6. Displaying the results

Usage:
    python test_rag_comprehensive.py [options]

Options:
    --api-url TEXT         Base URL for the API [default: http://localhost:8001/api/v1]
    --project-name TEXT    Name of the project to create [default: Test RAG Project]
    --scrape-url TEXT      URL to scrape [default: http://example.com]
    --query TEXT           Query to send to the RAG system
                           [default: What is the main topic of the scraped content?]
    --max-wait-attempts INT  Maximum number of attempts to wait for RAG processing [default: 10]
    --wait-interval INT    Time to wait between attempts in seconds [default: 2]
    --verbose              Enable verbose output
    --continue-on-error    Continue despite errors in some cases
    --help                 Show this message and exit.
"""

import requests
import json
import time
import uuid
import argparse
import sys
from datetime import datetime

# Default values
DEFAULT_API_URL = "http://localhost:8000/api/v1"
DEFAULT_MAX_WAIT_ATTEMPTS = 30
DEFAULT_WAIT_INTERVAL = 3

# Azure OpenAI credentials (already defined in test files)
AZURE_OPENAI_CREDENTIALS = {
    "api_key": "BuVHZw4d7OmEwH5QIsvw8gsKLyRxNUow4PT1gYg83iukV6JLRVL8JQQJ99BDACHYHv6XJ3w3AAAAACOGR8LC",
    "endpoint": "https://practicehub3994533910.services.ai.azure.com"
}

# Azure OpenAI model configuration
AZURE_EMBEDDING_MODEL = "text-embedding-ada-002"
AZURE_CHAT_MODEL = "gpt-4o-mini"

def print_separator():
    """Print a separator line."""
    print("\n" + "=" * 80 + "\n")

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

def check_api_availability(api_url, verbose=False):
    """Check if the API is available."""
    log_message("Checking API availability...", verbose=verbose)

    # Extract the base URL without the API version path
    base_url = api_url.split('/api/')[0]

    try:
        response = requests.get(f"{base_url}/health")
        response.raise_for_status()

        log_message("API is available.", verbose=verbose)
        return True
    except requests.exceptions.RequestException as e:
        handle_error("API is not available", e, exit_script=True)
        return False

def create_project(api_url, name="Test RAG Project", verbose=False):
    """Create a new project."""
    log_message(f"Creating a new project: {name}...", verbose=verbose)

    try:
        response = requests.post(
            f"{api_url}/projects",
            json={"name": name}
        )
        response.raise_for_status()

        project = response.json()
        log_message(f"Project created successfully with ID: {project['id']}", verbose=verbose)
        print(f"Project created: {json.dumps(project, indent=2)}")
        return project
    except requests.exceptions.RequestException as e:
        handle_error("Failed to create project", e, exit_script=True)
        return None

def enable_rag(api_url, project_id, verbose=False):
    """Enable RAG for the project."""
    log_message(f"Enabling RAG for project {project_id}...", verbose=verbose)

    try:
        response = requests.put(
            f"{api_url}/projects/{project_id}",
            json={"rag_enabled": True}
        )
        response.raise_for_status()

        project = response.json()
        log_message(f"RAG enabled successfully. Status: {project['rag_status']}", verbose=verbose)
        print(f"Project updated: {json.dumps(project, indent=2)}")
        return project
    except requests.exceptions.RequestException as e:
        handle_error("Failed to enable RAG", e, exit_script=True)
        return None

def execute_scrape(api_url, project_id, url="http://example.com", verbose=False):
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

        result = response.json()
        log_message(f"Scrape executed successfully. Status: {result['status']}", verbose=verbose)
        print(f"Scrape result: {json.dumps(result, indent=2)}")
        return session_id
    except requests.exceptions.RequestException as e:
        handle_error("Failed to execute scrape", e, exit_script=True)
        return None

def wait_for_rag_ingestion(api_url, project_id, session_id, max_attempts=10, wait_interval=2, verbose=False):
    """Wait for RAG ingestion to complete."""
    log_message(f"Waiting for RAG ingestion to complete for session {session_id}...", verbose=verbose)

    for attempt in range(max_attempts):
        try:
            response = requests.get(f"{api_url}/projects/{project_id}/sessions")
            response.raise_for_status()

            sessions = response.json()
            for session in sessions:
                if session["id"] == session_id:
                    log_message(f"Session status: {session['status']}", verbose=verbose)
                    if session["status"] == "rag_ingested":
                        log_message("RAG ingestion completed successfully!", verbose=verbose)
                        return True

            log_message(f"Attempt {attempt + 1}/{max_attempts}: RAG ingestion still in progress...", verbose=verbose)
            time.sleep(wait_interval)
        except requests.exceptions.RequestException as e:
            log_message(f"Error checking session status: {e}", level="WARNING", verbose=verbose)
            time.sleep(wait_interval)

    log_message("RAG ingestion did not complete within the expected time.", level="WARNING", verbose=verbose)
    return False

def query_rag(api_url, project_id, query="What is the main topic of the scraped content?", verbose=False):
    """Query the RAG system."""
    log_message(f"Querying RAG for project {project_id} with query: '{query}'...", verbose=verbose)

    try:
        # Create Azure credentials with specific chat deployment name
        azure_credentials = {
            **AZURE_OPENAI_CREDENTIALS,
            "deployment_name": AZURE_CHAT_MODEL
        }

        response = requests.post(
            f"{api_url}/projects/{project_id}/query-rag",
            json={
                "query": query,
                "model_deployment": AZURE_CHAT_MODEL,
                "azure_credentials": azure_credentials
            }
        )
        response.raise_for_status()

        result = response.json()
        log_message("RAG query executed successfully!", verbose=verbose)

        print("\nRAG Query Result:")
        print(f"Query: {query}")
        print(f"Answer: {result['answer']}")

        if result.get('source_documents'):
            print("\nSource Documents:")
            for i, doc in enumerate(result['source_documents'], 1):
                print(f"  {i}. {doc['metadata']['url']} (Similarity: {doc['metadata']['similarity']:.4f})")
                print(f"     Excerpt: {doc['content'][:100]}...")

            # Verify that the content is real and not dummy data
            dummy_content_markers = ["This is some dummy markdown content", "Item 1", "Item 2", "Sub-section"]
            has_real_content = True

            for doc in result['source_documents']:
                content = doc['content']
                for marker in dummy_content_markers:
                    if marker in content:
                        has_real_content = False
                        log_message(f"WARNING: Document contains dummy content marker: '{marker}'", level="WARNING", verbose=True)

            if has_real_content:
                log_message("SUCCESS: Documents contain real content from Firecrawl API!", verbose=True)
            else:
                log_message("WARNING: Some documents may still contain dummy content", level="WARNING", verbose=True)

        return result
    except requests.exceptions.RequestException as e:
        handle_error("Failed to query RAG", e, exit_script=True)
        return None

def main(args):
    """Main function to test RAG functionality."""
    start_time = datetime.now()

    print(f"Starting RAG functionality test at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API URL: {args.api_url}")
    print(f"Project Name: {args.project_name}")
    print(f"Scrape URL: {args.scrape_url}")
    print(f"Query: {args.query}")
    print_separator()

    # Check API availability
    check_api_availability(args.api_url, args.verbose)
    print_separator()

    # Step 1: Create a new project
    project = create_project(args.api_url, args.project_name, args.verbose)
    project_id = project["id"]
    print_separator()

    # Step 2: Enable RAG for the project
    enable_rag(args.api_url, project_id, args.verbose)
    print_separator()

    # Step 3: Execute a scrape operation
    session_id = execute_scrape(args.api_url, project_id, args.scrape_url, args.verbose)
    print_separator()

    # Step 4: Wait for the scrape to be processed
    rag_ingestion_success = wait_for_rag_ingestion(
        args.api_url, project_id, session_id,
        args.max_wait_attempts, args.wait_interval, args.verbose
    )

    if not rag_ingestion_success:
        if not args.continue_on_error:
            handle_error("RAG ingestion did not complete within the expected time.", exit_script=True)
        print("Continuing anyway despite RAG ingestion timeout...")

    print_separator()

    # Step 5: Query the RAG system
    rag_result = query_rag(args.api_url, project_id, args.query, args.verbose)
    print_separator()

    # Print summary
    end_time = datetime.now()
    duration = end_time - start_time

    print("RAG Functionality Test Summary:")
    print(f"Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Completed at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Duration: {duration.total_seconds():.2f} seconds")
    print(f"Project ID: {project_id}")
    print(f"Session ID: {session_id}")
    print(f"RAG Ingestion: {'Successful' if rag_ingestion_success else 'Timed out'}")
    print(f"RAG Query: {'Successful' if rag_result else 'Failed'}")

    print("\nRAG functionality test completed successfully!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test RAG functionality")
    parser.add_argument("--api-url", default=DEFAULT_API_URL, help=f"Base URL for the API [default: {DEFAULT_API_URL}]")
    parser.add_argument("--project-name", default="Test RAG Project", help="Name of the project to create")
    parser.add_argument("--scrape-url", default="https://en.wikipedia.org/wiki/Retrieval-augmented_generation", help="URL to scrape")
    parser.add_argument("--query", default="What is the main topic of the scraped content?", help="Query to send to the RAG system")
    parser.add_argument("--max-wait-attempts", type=int, default=DEFAULT_MAX_WAIT_ATTEMPTS, help=f"Maximum number of attempts to wait for RAG processing [default: {DEFAULT_MAX_WAIT_ATTEMPTS}]")
    parser.add_argument("--wait-interval", type=int, default=DEFAULT_WAIT_INTERVAL, help=f"Time to wait between attempts in seconds [default: {DEFAULT_WAIT_INTERVAL}]")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("--continue-on-error", action="store_true", help="Continue despite errors in some cases")

    args = parser.parse_args()

    try:
        main(args)
    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
        sys.exit(1)
    except Exception as e:
        handle_error("Unexpected error", e, exit_script=True)
