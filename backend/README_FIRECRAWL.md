# Firecrawl API Integration

This document provides instructions for setting up and using the Firecrawl API integration for web scraping in our RAG system.

## Overview

The Firecrawl API integration replaces the simulated web scraping functionality with actual web scraping capabilities. It uses the Firecrawl API to fetch web content, which is then processed by our existing RAG pipeline.

## Setup

### 1. Get a Firecrawl API Key

1. Sign up for a Firecrawl account at [https://firecrawl.dev](https://firecrawl.dev)
2. Navigate to your account settings to get your API key

### 2. Configure Environment Variables

Add your Firecrawl API key to the `.env` file in the `backend` directory:

```
FIRECRAWL_API_KEY=your_firecrawl_api_key
```

A template for this is provided in the `.env.example` file.

## Usage

The integration is seamless with the existing API. When you call the `/projects/{project_id}/execute-scrape` endpoint, it will now use the Firecrawl API to fetch the content from the specified URL.

### API Endpoint

```
POST /api/v1/projects/{project_id}/execute-scrape
```

Request body:
```json
{
  "current_page_url": "https://example.com",
  "session_id": "unique-session-id",
  "api_keys": {
    "api_key": "your-azure-openai-api-key",
    "endpoint": "https://your-resource-name.openai.azure.com",
    "deployment_name": "text-embedding-ada-002"
  }
}
```

## Testing

You can test the Firecrawl API integration using the `test_rag_comprehensive.py` script:

```bash
python test_rag_comprehensive.py --scrape-url "https://en.wikipedia.org/wiki/Retrieval-augmented_generation" --query "What is RAG?"
```

This script will:
1. Create a new project
2. Enable RAG for the project
3. Execute a scrape operation on the specified URL using the Firecrawl API
4. Wait for the scrape to be processed
5. Query the RAG system with the specified question
6. Display the results
7. Verify that real content is being scraped rather than dummy data

## Error Handling

The integration includes proper error handling for Firecrawl API calls, including:

- Authentication failures
- Rate limits
- Timeouts
- Invalid URLs
- Other API errors

If an error occurs during scraping, the error message will be returned in the response.

## Firecrawl API Features

The Firecrawl API provides several features that can be used to enhance the scraping functionality:

- **Clean Markdown**: Converts web pages into clean markdown, ideal for LLM applications
- **Structured Data**: Extracts structured data from web pages
- **Metadata**: Provides metadata about the scraped page, such as title, description, and language
- **Proxy Support**: Handles proxies, caching, and rate limits
- **Dynamic Content**: Handles dynamic websites, JavaScript-rendered sites, PDFs, and images

For more information about the Firecrawl API, see the [official documentation](https://docs.firecrawl.dev/).

## Limitations

- The Firecrawl API has rate limits and usage quotas. Check the [Firecrawl documentation](https://docs.firecrawl.dev/rate-limits) for details.
- Some websites may block scraping attempts. The Firecrawl API includes features to handle this, but it may not work for all websites.
- The API key should be kept secure and not exposed in client-side code.

## Troubleshooting

If you encounter issues with the Firecrawl API integration, check the following:

1. Verify that your Firecrawl API key is correctly set in the `.env` file
2. Check that the URL you're trying to scrape is accessible and not blocked
3. Ensure that your Firecrawl account has sufficient credits for scraping
4. Check the backend logs for detailed error messages

For more help, contact the Firecrawl support team or refer to their [documentation](https://docs.firecrawl.dev/).
