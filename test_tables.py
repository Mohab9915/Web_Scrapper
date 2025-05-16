"""
Script to test if the tables were created successfully.
"""
import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv("backend/.env")

# Supabase credentials
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

print(f"Supabase URL: {SUPABASE_URL}")
print(f"Supabase Key: {SUPABASE_KEY[:10]}...{SUPABASE_KEY[-10:]}")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def test_tables():
    """Test if the tables were created successfully."""
    print("Testing if tables were created successfully...")
    
    # Test projects table
    try:
        print("\nTesting projects table...")
        response = supabase.table('projects').select('*').limit(5).execute()
        print(f"Projects: {response.data}")
        print("Projects table exists!")
    except Exception as e:
        print(f"Error querying projects table: {e}")
    
    # Test scrape_sessions table
    try:
        print("\nTesting scrape_sessions table...")
        response = supabase.table('scrape_sessions').select('*').limit(5).execute()
        print(f"Scrape sessions: {response.data}")
        print("Scrape sessions table exists!")
    except Exception as e:
        print(f"Error querying scrape_sessions table: {e}")
    
    # Test markdowns table
    try:
        print("\nTesting markdowns table...")
        response = supabase.table('markdowns').select('*').limit(5).execute()
        print(f"Markdowns: {response.data}")
        print("Markdowns table exists!")
    except Exception as e:
        print(f"Error querying markdowns table: {e}")
    
    # Test embeddings table
    try:
        print("\nTesting embeddings table...")
        response = supabase.table('embeddings').select('*').limit(5).execute()
        print(f"Embeddings: {response.data}")
        print("Embeddings table exists!")
    except Exception as e:
        print(f"Error querying embeddings table: {e}")
    
    # Test match_embeddings_filtered function
    try:
        print("\nTesting match_embeddings_filtered function...")
        # We can't directly test the function without data, but we can check if it exists
        print("Note: We can't directly test the function without data.")
        print("Please check in the Supabase UI if the function was created successfully.")
    except Exception as e:
        print(f"Error testing match_embeddings_filtered function: {e}")

if __name__ == "__main__":
    test_tables()
