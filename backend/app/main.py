"""
FastAPI application entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api import projects, scraping, rag, websockets, cache, project_urls, history, project_settings
from .config import settings
from .services.scraping_service import ScrapingService
from uuid import UUID
from fastapi import Depends
# Import diagnostics separately to avoid module not found errors
try:
    from .api import diagnostics
except ImportError:
    print("Warning: Diagnostics module not available")

app = FastAPI(
    title="Interactive Agentic Web Scraper & RAG System API",
    description="Backend API for the Interactive Agentic Web Scraper & RAG System",
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:9002",
        "http://localhost:9003",
        "http://localhost:9004",
        "https://scrapemaster-frontend-prod.whitemeadow-57a6711f.eastus.azurecontainerapps.io",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:9002",
        "http://127.0.0.1:9003",
        "http://127.0.0.1:9004"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(projects.router, prefix=settings.API_V1_STR)
app.include_router(scraping.router, prefix=settings.API_V1_STR)
app.include_router(rag.router, prefix=settings.API_V1_STR)
app.include_router(websockets.router, prefix=settings.API_V1_STR)
app.include_router(cache.router, prefix=settings.API_V1_STR)
app.include_router(project_urls.router, prefix=settings.API_V1_STR)
app.include_router(history.router, prefix=settings.API_V1_STR)
app.include_router(project_settings.router, prefix=settings.API_V1_STR, tags=["Project Settings"])

# Include diagnostics router if available
try:
    if hasattr(diagnostics, 'router'):
        app.include_router(diagnostics.router, prefix=settings.API_V1_STR)
        print("Diagnostics endpoints enabled")
except (NameError, AttributeError) as e:
    print(f"Warning: Diagnostics endpoints not available: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint for deployment monitoring."""
    return {
        "status": "healthy",
        "service": "Interactive Agentic Web Scraper & RAG System API",
        "version": "0.1.0",
        "timestamp": "2024-01-01T00:00:00Z"
    }

# Add download endpoint without API prefix
@app.get("/download/{project_id}/{session_id}/{format}")
async def download_scraped_data(
    project_id: UUID,
    session_id: UUID,
    format: str,
    scraping_service: ScrapingService = Depends()
):
    """
    Download scraped data in JSON, CSV, or PDF format.
    This endpoint is not prefixed with /api/v1 to match frontend expectations.
    """
    from fastapi import HTTPException

    if format not in ["json", "csv", "pdf"]:
        raise HTTPException(status_code=400, detail="Invalid format. Must be 'json', 'csv', or 'pdf'")

    return await scraping_service.get_download_file(project_id, session_id, format)

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler with improved error messages."""
    error_message = str(exc)

    # Handle common database errors
    if "PGRST116" in error_message and "0 rows" in error_message:
        return JSONResponse(
            status_code=404,
            content={"detail": "Resource not found. Please check if the project or session exists."}
        )

    # Handle URL validation errors
    if "NoneType" in error_message and "data" in error_message:
        return JSONResponse(
            status_code=400,
            content={"detail": "Invalid URL or request data. Please check your input and try again."}
        )

    # Handle connection errors
    if "connection" in error_message.lower() or "timeout" in error_message.lower():
        return JSONResponse(
            status_code=503,
            content={"detail": "Service temporarily unavailable. Please try again later."}
        )

    # Default error response
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please contact support if the problem persists."}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
