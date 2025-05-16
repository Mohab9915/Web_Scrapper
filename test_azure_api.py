"""
Test script to directly test the Azure AI Studio API.
"""
import requests
import json

# Azure AI Studio configuration
AZURE_API_KEY = "BuVHZw4d7OmEwH5QIsvw8gsKLyRxNUow4PT1gYg83iukV6JLRVL8JQQJ99BDACHYHv6XJ3w3AAAAACOGR8LC"
AZURE_ENDPOINT = "https://practicehub3994533910.services.ai.azure.com"  # Remove /models

def test_embedding_api():
    """Test the embedding API."""
    print("Testing embedding API...")

    # Embedding API URL - try different formats
    # Format 1: Azure OpenAI format
    url = f"{AZURE_ENDPOINT}/openai/deployments/text-embedding-ada-002/embeddings?api-version=2023-05-15"
    print(f"Trying URL: {url}")

    # Request payload
    payload = {
        "input": "This is a test."
    }

    # Make the request
    response = requests.post(
        url,
        json=payload,
        headers={
            "Content-Type": "application/json",
            "api-key": AZURE_API_KEY
        }
    )

    print(f"Status code: {response.status_code}")
    if response.status_code == 200:
        # Print the first 5 embedding values
        embedding = response.json().get("data", [{}])[0].get("embedding", [])
        print(f"Embedding (first 5 values): {embedding[:5]}")
    else:
        print(f"Error: {response.text}")

    print("\n" + "=" * 80 + "\n")

def test_chat_api():
    """Test the chat API."""
    print("Testing chat API...")

    # Chat API URL - try different formats
    # Format 1: Azure OpenAI format
    url = f"{AZURE_ENDPOINT}/openai/deployments/gpt-4o-mini/chat/completions?api-version=2023-05-15"
    print(f"Trying URL: {url}")

    # Request payload
    payload = {
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant."
            },
            {
                "role": "user",
                "content": "What is the capital of France?"
            }
        ],
        "temperature": 0.2,
        "top_p": 0.8,
        "max_tokens": 1024
    }

    # Make the request
    response = requests.post(
        url,
        json=payload,
        headers={
            "Content-Type": "application/json",
            "api-key": AZURE_API_KEY
        }
    )

    print(f"Status code: {response.status_code}")
    if response.status_code == 200:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    else:
        print(f"Error: {response.text}")

    print("\n" + "=" * 80 + "\n")

if __name__ == "__main__":
    test_embedding_api()
    test_chat_api()
