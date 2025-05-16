"""
Database connection and initialization.
"""
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def get_supabase_client() -> Client:
    """
    Create and return a Supabase client.
    
    Returns:
        Client: Supabase client
    
    Raises:
        ValueError: If SUPABASE_URL or SUPABASE_KEY is not set
    """
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
    
    return create_client(SUPABASE_URL, SUPABASE_KEY)

# Create a global Supabase client instance
supabase = get_supabase_client()
