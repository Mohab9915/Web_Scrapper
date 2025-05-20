"""
Configuration settings for the application.
"""
import os
from typing import List
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    """Application settings."""

    # API settings
    API_V1_STR: str = "/api/v1"

    # CORS settings
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:9002", "http://localhost:9003", "http://localhost:9004"]

    # Supabase settings
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")

    # Browser control settings
    BROWSER_CONTROL_TYPE: str = os.getenv("BROWSER_CONTROL_TYPE", "simulated")  # 'simulated', 'puppeteer', 'browserless'
    BROWSERLESS_API_KEY: str = os.getenv("BROWSERLESS_API_KEY", "")

    # RAG settings
    EMBEDDING_BATCH_SIZE: int = int(os.getenv("EMBEDDING_BATCH_SIZE", "20"))  # Number of chunks to process in a single API call
    WEB_CACHE_EXPIRY_HOURS: int = int(os.getenv("WEB_CACHE_EXPIRY_HOURS", "24"))  # Cache expiry time in hours

    # Firecrawl API settings
    FIRECRAWL_API_KEY: str = os.getenv("FIRECRAWL_API_KEY", "")

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
