"""
Configuration settings for the application.
"""
import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    """Application settings."""

    # API settings
    API_V1_STR: str = "/api/v1"

    # CORS settings (comma-separated list, e.g. "http://localhost:9002,http://localhost:3000").
    # Leave empty to let `main.py` fall back to sensible dev defaults.
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "")

    # Supabase settings
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")

    # Browser control settings
    BROWSER_CONTROL_TYPE: str = os.getenv("BROWSER_CONTROL_TYPE", "simulated")  # 'simulated', 'puppeteer', 'browserless'
    BROWSERLESS_API_KEY: str = os.getenv("BROWSERLESS_API_KEY", "")

    # RAG settings
    EMBEDDING_BATCH_SIZE: int = int(os.getenv("EMBEDDING_BATCH_SIZE", "20"))  # Number of chunks to process in a single API call
    WEB_CACHE_EXPIRY_HOURS: int = int(os.getenv("WEB_CACHE_EXPIRY_HOURS", "24"))  # Cache expiry time in hours

    # Timeout settings
    SCRAPING_TIMEOUT: int = int(os.getenv("SCRAPING_TIMEOUT", "600"))  # 10 minutes default
    PAGE_LOAD_TIMEOUT: int = int(os.getenv("PAGE_LOAD_TIMEOUT", "300"))  # 5 minutes default
    SCRIPT_TIMEOUT: int = int(os.getenv("SCRIPT_TIMEOUT", "120"))  # 2 minutes default

    # Web scraping settings (using Crawl4AI)
    # No API key needed for Crawl4AI as it runs locally
    
    # Azure OpenAI settings
    AZURE_OPENAI_ENDPOINT: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    AZURE_OPENAI_API_KEY: str = os.getenv("AZURE_OPENAI_API_KEY", "")
    AZURE_OPENAI_API_VERSION: str = os.getenv("AZURE_OPENAI_API_VERSION", "")
    AZURE_OPENAI_MODEL: str = os.getenv("AZURE_OPENAI_MODEL", "")
    AZURE_CHAT_MODEL: str = os.getenv("AZURE_CHAT_MODEL", "gpt-4o")
    AZURE_EMBEDDING_MODEL: str = os.getenv("AZURE_EMBEDDING_MODEL", "text-embedding-ada-002")
    
    # OpenAI settings
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODELS: str = os.getenv("OPENAI_MODELS", "[]")

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Allow extra environment variables (e.g., REACT_APP_* for frontend)

settings = Settings()
