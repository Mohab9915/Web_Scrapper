#!/bin/bash

# Get the project ID
PROJECT_ID=$(curl -s http://localhost:8001/api/v1/projects | jq -r '.[0].id')
echo "Using project ID: $PROJECT_ID"

# Enable RAG for the project
echo -e "\nEnabling RAG for project $PROJECT_ID..."
curl -X PUT \
  -H "Content-Type: application/json" \
  -d '{"rag_enabled": true}' \
  http://localhost:8001/api/v1/projects/$PROJECT_ID

# Execute a scrape
echo -e "\n\nExecuting scrape for project $PROJECT_ID..."
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "current_page_url": "http://example.com",
    "session_id": "test-session-id",
    "api_keys": {
      "api_key": "test-api-key",
      "endpoint": "https://test-endpoint.openai.azure.com"
    }
  }' \
  http://localhost:8001/api/v1/projects/$PROJECT_ID/execute-scrape

# Query RAG
echo -e "\n\nQuerying RAG for project $PROJECT_ID..."
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the main topic of the scraped content?",
    "model_deployment": "gpt-35-turbo",
    "azure_credentials": {
      "api_key": "test-api-key",
      "endpoint": "https://test-endpoint.openai.azure.com"
    }
  }' \
  http://localhost:8001/api/v1/projects/$PROJECT_ID/query-rag
