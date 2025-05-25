# Crawl4AI Integration

## Overview

This application uses the Crawl4AI framework for web scraping, replacing the previous Firecrawl API solution. Crawl4AI is a powerful Python framework specifically designed for web scraping with features like automatic content filtering, JavaScript rendering, and structured data extraction.

## Features

- **High-quality content extraction**: Crawl4AI intelligently extracts the main content from web pages, filtering out ads, navigation menus, and other irrelevant elements
- **JavaScript rendering**: Full support for pages that rely on JavaScript for content loading
- **Markdown conversion**: Web pages are automatically converted to clean, structured markdown
- **Content filtering**: Built-in PruningContentFilter to focus on the most relevant content
- **Caching**: Web page content is cached to improve performance and reduce redundant scraping

## Implementation

The Crawl4AI integration is implemented in `backend/app/utils/crawl4ai_crawler.py` with two main functions:

1. `scrape_url()`: Scrapes a web page and returns its content as markdown and/or HTML
2. `extract_structured_data()`: Extracts structured data from a web page using either CSS selectors or LLM-based extraction

These functions maintain the same interface as the previous Firecrawl API functions, making the transition seamless.

## Configuration

Crawl4AI is configured with the following settings:

- **Browser configuration**:
  - Headless mode enabled
  - JavaScript enabled for dynamic pages
  - Images disabled for faster loading
  - Custom user agent
  - 120-second timeout

- **Crawler configuration**:
  - Configurable cache mode
  - Content filtering with PruningContentFilter
  - Markdown generation with DefaultMarkdownGenerator

## Caching

Just like with the previous API, the caching system stores web page content in the Supabase `web_cache` table. This:

- Reduces redundant scraping of the same URLs
- Improves application performance
- Minimizes load on target websites

The cache system includes:
- Time-based expiration (configurable via settings)
- Force refresh capability
- Cache statistics tracking

## Usage Example

```python
from app.utils.crawl4ai_crawler import scrape_url

# Scrape a URL with caching
result = await scrape_url(
    "https://example.com",
    formats=["markdown", "html"],
    force_refresh=False
)

# Extract markdown content
markdown_content = result.get("markdown", "")

# Get metadata
metadata = result.get("metadata", {})
page_title = metadata.get("title", "Untitled Page")
```

## Structured Data Extraction

Crawl4AI supports multiple methods for extracting structured data:

1. **CSS-based extraction**: Using JsonCssExtractionStrategy with a schema that defines selectors for data fields
2. **LLM-based extraction**: Using LLMExtractionStrategy with a natural language prompt
3. **Pattern-based extraction**: Using RegexExtractionStrategy for extracting common data types

Example:

```python
from app.utils.crawl4ai_crawler import extract_structured_data

# Define a schema for CSS-based extraction
schema = {
    "name": "Product Details",
    "baseSelector": "div.product",
    "fields": [
        {"name": "title", "selector": "h1.product-title", "type": "text"},
        {"name": "price", "selector": "span.price", "type": "text"},
        {"name": "description", "selector": "div.description", "type": "text"}
    ]
}

# Extract structured data using the schema
result = await extract_structured_data(
    "https://example.com/product",
    schema=schema
)

# Or use a natural language prompt for LLM-based extraction
result = await extract_structured_data(
    "https://example.com/product",
    prompt="Extract the product title, price, and description."
)

# Access the extracted JSON data
structured_data = result.get("json", {})
```

## Comparison with Previous API

| Feature | Firecrawl API | Crawl4AI Framework |
|---------|--------------|--------------------|
| JavaScript support | Yes | Yes |
| Content filtering | Limited | Advanced (multiple strategies) |
| Structured extraction | Limited | Multiple methods (CSS, XPath, LLM, Regex) |
| Dependency | External API | Local framework |
| Cost | API pricing | Free, open-source |
| Customization | Limited | Highly customizable |
| Performance | API-dependent | Local processing control |

## Additional Resources

For more information about Crawl4AI, visit:
- Documentation: https://docs.crawl4ai.com/
- GitHub Repository: https://github.com/unclecode/crawl4ai