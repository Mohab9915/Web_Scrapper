# Interactive Agentic Web Scraper & RAG System - Backend

This is the Python backend for the Interactive Agentic Web Scraper & RAG System. It provides API endpoints for managing projects, interactive web scraping, and RAG functionality.

## Features

- Project management (CRUD operations)
- Interactive web scraping with browser control
- RAG functionality (ingestion, embedding, querying)
- Structured data extraction from scraped content
- API endpoints for frontend integration

## Technologies

- FastAPI for the web framework
- Supabase (PostgreSQL with pgvector) for the database
- Azure OpenAI Service for embeddings and LLM
- Crawl4AI for web scraping
- Browser control via Puppeteer/Playwright or Browserless.io

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py               # Configuration settings
│   ├── database.py             # Database connection and initialization
│   ├── api/                    # API routes
│   │   ├── __init__.py
│   │   ├── projects.py         # Project management endpoints
│   │   ├── scraping.py         # Scraping endpoints
│   │   └── rag.py              # RAG query endpoints
│   ├── models/                 # Pydantic models for request/response
│   │   ├── __init__.py
│   │   ├── project.py
│   │   ├── scrape_session.py
│   │   └── chat.py
│   ├── services/               # Business logic
│   │   ├── __init__.py
│   │   ├── project_service.py
│   │   ├── scraping_service.py
│   │   └── rag_service.py
│   └── utils/                  # Utility functions
│       ├── __init__.py
│       ├── browser_control.py  # Browser control logic
│       ├── text_processing.py  # Text chunking and processing
│       └── embedding.py        # Embedding generation
├── migrations/                 # Database migrations
├── tests/                      # Unit and integration tests
├── .env                        # Environment variables
├── requirements.txt            # Dependencies
└── README.md                   # Documentation
```

## Setup

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Unix/MacOS: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Create a `.env` file with the required environment variables (see below)
6. Run the application: `python -m app.main`

## API Documentation

Once the application is running, you can access the API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Database Setup

The application requires a Supabase project with the following setup:

1. Create a new Supabase project
2. Enable the pgvector extension
3. Run the SQL scripts in the `migrations` directory to set up the tables and functions

## Environment Variables

Create a `.env` file in the root directory with the following variables:

```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
BROWSER_CONTROL_TYPE=simulated
BROWSERLESS_API_KEY=your_browserless_api_key_if_using
```

Note: Azure OpenAI credentials are not stored in environment variables. They should be passed from the frontend with each request for security reasons. The credentials should include:
- `api_key`: Your Azure OpenAI API key
- `endpoint`: Your Azure OpenAI endpoint URL (e.g., https://your-resource-name.openai.azure.com)
- `deployment_name`: (Optional) The name of your model deployment (defaults to "gpt-35-turbo" for chat and "text-embedding-ada-002" for embeddings)

## API Endpoints

### Project Management

- `GET /projects` - Get all projects
- `POST /projects` - Create a new project
- `GET /projects/{project_id}` - Get a specific project
- `PUT /projects/{project_id}` - Update a project
- `DELETE /projects/{project_id}` - Delete a project

### Scraping

- `GET /projects/{project_id}/sessions` - Get all scraped sessions for a project
- `POST /projects/{project_id}/initiate-interactive-scrape` - Start an interactive scraping session
- `POST /projects/{project_id}/execute-scrape` - Execute scraping on a specific URL
- `DELETE /projects/{project_id}/sessions/{session_id}` - Delete a scraped session
- `GET /download/{project_id}/{session_id}/{format}` - Download scraped data in JSON or CSV format

### RAG

- `GET /projects/{project_id}/chat` - Get chat messages for a project
- `POST /projects/{project_id}/query-rag` - Query the RAG system
- `POST /projects/{project_id}/chat` - Post a new chat message
# Web-Scraping-Agent
