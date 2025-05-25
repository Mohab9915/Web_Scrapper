"""
Script to enable RAG for a project.
"""
import requests
import sys

def enable_rag(project_id):
    """
    Enable RAG for a project.
    
    Args:
        project_id (str): Project ID
    """
    url = f"http://localhost:8000/api/v1/projects/{project_id}/enable-rag"
    response = requests.post(url)
    
    if response.status_code == 200:
        print(f"RAG enabled for project {project_id}")
        print(response.json())
    else:
        print(f"Error enabling RAG for project {project_id}")
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python enable_rag.py <project_id>")
        sys.exit(1)
    
    project_id = sys.argv[1]
    enable_rag(project_id)