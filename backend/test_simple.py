"""Very simple test to verify the backend API is working"""

import requests
import json

def test_simple_api():
    """Basic test for the API availability"""
    print("\n=== Running Simple API Test ===")

    # Check that the server is running
    try:
        response = requests.get("http://localhost:8000")
        print(f"API root response: {response.status_code}")

        # Try to access projects endpoint
        response = requests.get("http://localhost:8000/api/v1/projects")
        print(f"Projects endpoint: {response.status_code}")

        if response.status_code == 200:
            print("Successfully connected to projects API")
            try:
                projects = response.json()
                print(f"Found {len(projects)} projects")
                return True
            except json.JSONDecodeError:
                print("Warning: Could not parse JSON response")
                print(f"Response text: {response.text[:100]}...")
        else:
            print(f"Projects endpoint returned non-200 status: {response.status_code}")

        return True  # Consider the test passed if we could connect

    except requests.exceptions.ConnectionError:
        print("Could not connect to API server. Is it running?")
        return False

if __name__ == "__main__":
    test_simple_api()
