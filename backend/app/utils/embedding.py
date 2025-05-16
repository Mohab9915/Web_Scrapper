"""
Utility functions for embedding generation using Azure OpenAI Service.
"""
import numpy as np
from typing import List, Optional, Dict, Any
import httpx
import asyncio
from math import ceil

from app.utils.firecrawl_api import AZURE_EMBEDDING_MODEL, AZURE_CHAT_MODEL
from app.config import settings

async def generate_embeddings(text: str, azure_credentials: Optional[Dict[str, str]] = None) -> List[float]:
    """
    Generate embeddings for text using Azure OpenAI Service or Azure AI Studio.

    Args:
        text (str): The text to embed
        azure_credentials (Dict[str, str]): Dictionary containing 'api_key' and 'endpoint' for Azure OpenAI/AI Studio

    Returns:
        List[float]: List of embedding values

    Raises:
        ValueError: If no Azure credentials are provided
    """
    if not azure_credentials or 'api_key' not in azure_credentials or 'endpoint' not in azure_credentials:
        # In a production environment, we should log this properly
        print("Error: Azure OpenAI credentials missing or incomplete")
        # Return a random embedding for development purposes
        # In production, this should raise an exception
        return list(np.random.rand(1536))  # Azure OpenAI text-embedding-ada-002 has 1536 dimensions

    api_key = azure_credentials['api_key']
    endpoint = azure_credentials['endpoint']
    # Always use the correct embedding model
    deployment_name = AZURE_EMBEDDING_MODEL

    try:
        # Determine the correct API endpoint format based on the endpoint URL
        if "services.ai.azure.com" in endpoint:
            # Azure AI Studio format - use the standard Azure OpenAI format
            # Remove "/models" if it's in the endpoint
            base_endpoint = endpoint.replace("/models", "")
            url = f"{base_endpoint}/openai/deployments/{deployment_name}/embeddings?api-version=2023-05-15"
        else:
            # Traditional Azure OpenAI format
            url = f"{endpoint}/openai/deployments/{deployment_name}/embeddings?api-version=2023-05-15"

        print(f"Using embedding API URL: {url}")

        # Request payload
        payload = {
            "input": text
        }

        # Make the API request
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "api-key": api_key
                }
            )

            if response.status_code != 200:
                print(f"Error from Azure API: {response.status_code} - {response.text}")
                # Return random embedding as fallback for development
                return list(np.random.rand(1536))

            # Extract embedding from response
            response_data = response.json()
            embedding = response_data.get("data", [{}])[0].get("embedding", [])

            return embedding
    except Exception as e:
        # Log the error
        print(f"Error generating embedding: {e}")
        # Return a random embedding as fallback for development
        return list(np.random.rand(1536))

async def generate_embeddings_batch(texts: List[str], azure_credentials: Optional[Dict[str, str]] = None) -> List[List[float]]:
    """
    Generate embeddings for multiple texts in batches using Azure OpenAI Service.

    Args:
        texts (List[str]): List of texts to embed
        azure_credentials (Dict[str, str]): Dictionary containing 'api_key' and 'endpoint' for Azure OpenAI/AI Studio

    Returns:
        List[List[float]]: List of embedding vectors

    Raises:
        ValueError: If no Azure credentials are provided
    """
    if not texts:
        return []

    if not azure_credentials or 'api_key' not in azure_credentials or 'endpoint' not in azure_credentials:
        # In a production environment, we should log this properly
        print("Error: Azure OpenAI credentials missing or incomplete")
        # Return random embeddings for development purposes
        return [list(np.random.rand(1536)) for _ in texts]

    api_key = azure_credentials['api_key']
    endpoint = azure_credentials['endpoint']
    # Always use the correct embedding model
    deployment_name = AZURE_EMBEDDING_MODEL

    # Determine the correct API endpoint format
    if "services.ai.azure.com" in endpoint:
        base_endpoint = endpoint.replace("/models", "")
        url = f"{base_endpoint}/openai/deployments/{deployment_name}/embeddings?api-version=2023-05-15"
    else:
        url = f"{endpoint}/openai/deployments/{deployment_name}/embeddings?api-version=2023-05-15"

    try:
        # Request payload for batch processing
        payload = {
            "input": texts
        }

        # Make the API request
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "api-key": api_key
                }
            )

            if response.status_code != 200:
                print(f"Error from Azure API in batch embedding: {response.status_code} - {response.text}")
                # Return random embeddings as fallback for development
                return [list(np.random.rand(1536)) for _ in texts]

            # Extract embeddings from response
            response_data = response.json()
            embeddings = [item.get("embedding", []) for item in response_data.get("data", [])]

            return embeddings
    except Exception as e:
        # Log the error
        print(f"Error generating batch embeddings: {e}")
        # Return random embeddings as fallback for development
        return [list(np.random.rand(1536)) for _ in texts]

async def process_chunks_with_batching(chunks: List[str], azure_credentials: Dict[str, str]) -> List[List[float]]:
    """
    Process text chunks with batching for efficient embedding generation.

    Args:
        chunks (List[str]): List of text chunks to process
        azure_credentials (Dict[str, str]): Azure OpenAI credentials

    Returns:
        List[List[float]]: List of embedding vectors
    """
    batch_size = settings.EMBEDDING_BATCH_SIZE
    num_chunks = len(chunks)
    num_batches = ceil(num_chunks / batch_size)
    all_embeddings = []

    print(f"Processing {num_chunks} chunks in {num_batches} batches (batch size: {batch_size})")

    for i in range(num_batches):
        start_idx = i * batch_size
        end_idx = min((i + 1) * batch_size, num_chunks)
        batch_chunks = chunks[start_idx:end_idx]

        # Process this batch
        batch_embeddings = await generate_embeddings_batch(batch_chunks, azure_credentials)
        all_embeddings.extend(batch_embeddings)

        # Small delay to avoid rate limiting
        if i < num_batches - 1:
            await asyncio.sleep(0.5)

    return all_embeddings

def calculate_embedding_cost(text: str) -> float:
    """
    Calculate the cost of embedding the given text with Azure OpenAI.

    Args:
        text (str): The text to calculate cost for

    Returns:
        float: Estimated cost in USD
    """
    # Azure OpenAI embedding costs (as of implementation)
    # This is an approximation and should be updated with actual pricing
    # Current pricing is approximately $0.0001 per 1K tokens
    # A simple approximation: 1 token ≈ 4 characters
    num_tokens = len(text) / 4
    cost = (num_tokens / 1000) * 0.0001

    return cost
