"""
Test script to create a project.
"""
import requests
import json

# Backend API URL
API_URL = "http://localhost:8001/api/v1"

def create_project():
    """Create a new project."""
    print("Creating a new project...")
    
    # Project data
    project_data = {
        "name": "Test Project"
    }
    
    # Make the request
    response = requests.post(
        f"{API_URL}/projects",
        json=project_data
    )
    
    # Check the response
    if response.status_code == 201:
        print("Project created successfully!")
        print(f"Project data: {json.dumps(response.json(), indent=2)}")
        return response.json()
    else:
        print(f"Error creating project: {response.status_code}")
        print(f"Response: {response.text}")
        return None

def get_projects():
    """Get all projects."""
    print("\nGetting all projects...")
    
    # Make the request
    response = requests.get(f"{API_URL}/projects")
    
    # Check the response
    if response.status_code == 200:
        print("Projects retrieved successfully!")
        print(f"Projects: {json.dumps(response.json(), indent=2)}")
        return response.json()
    else:
        print(f"Error getting projects: {response.status_code}")
        print(f"Response: {response.text}")
        return None

if __name__ == "__main__":
    project = create_project()
    projects = get_projects()
