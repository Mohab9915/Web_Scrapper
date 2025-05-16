"""
Test script to check scrape sessions.
"""
import requests
import json

# Backend API URL
API_URL = "http://localhost:8001/api/v1"

def get_project_id():
    """Get the project ID."""
    response = requests.get(f"{API_URL}/projects")
    if response.status_code == 200:
        projects = response.json()
        if projects:
            return projects[0]["id"]
    return None

def get_sessions(project_id):
    """Get all scrape sessions for a project."""
    print(f"Getting scrape sessions for project {project_id}...")
    
    response = requests.get(f"{API_URL}/projects/{project_id}/sessions")
    
    print(f"Status code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2) if response.status_code == 200 else response.text}")

if __name__ == "__main__":
    project_id = get_project_id()
    if project_id:
        print(f"Using project ID: {project_id}")
        get_sessions(project_id)
    else:
        print("No projects found. Please create a project first.")
