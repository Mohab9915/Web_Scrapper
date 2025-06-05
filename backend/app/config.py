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
    CORS_ORIGINS: str = "*"  # Allow all origins for now to fix CORS issue

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

settings = Settings()
