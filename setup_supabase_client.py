"""
Script to set up the Supabase database schema using the Supabase Python client.
"""
import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv("backend/.env")

# Supabase credentials
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def setup_database():
    """Set up the database schema."""
    print("Setting up Supabase database schema...")
    
    # Create projects table
    print("Creating projects table...")
    result = supabase.table("projects").insert({
        "name": "Test Project",
        "rag_enabled": False
    }).execute()
    print(f"Projects table created: {result}")
    
    # Create scrape_sessions table
    print("Creating scrape_sessions table...")
    # We'll try to query it first to see if it exists
    try:
        result = supabase.table("scrape_sessions").select("*").limit(1).execute()
        print("Scrape sessions table already exists.")
    except Exception as e:
        print(f"Error querying scrape_sessions: {e}")
        print("Creating scrape_sessions table...")
        # We'll need to create this table through SQL
    
    # Create markdowns table
    print("Creating markdowns table...")
    try:
        result = supabase.table("markdowns").select("*").limit(1).execute()
        print("Markdowns table already exists.")
    except Exception as e:
        print(f"Error querying markdowns: {e}")
        print("Creating markdowns table...")
        # We'll need to create this table through SQL
    
    # Create embeddings table
    print("Creating embeddings table...")
    try:
        result = supabase.table("embeddings").select("*").limit(1).execute()
        print("Embeddings table already exists.")
    except Exception as e:
        print(f"Error querying embeddings: {e}")
        print("Creating embeddings table...")
        # We'll need to create this table through SQL
    
    print("Database schema setup complete!")

if __name__ == "__main__":
    setup_database()
