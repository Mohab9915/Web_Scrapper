"""
Script to test the connection to Supabase.
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

def test_connection():
    """Test the connection to Supabase."""
    print("Testing connection to Supabase...")
    
    try:
        # Try to get the server version
        response = supabase.rpc('get_server_version').execute()
        print(f"Server version: {response}")
        print("Connection successful!")
    except Exception as e:
        print(f"Error connecting to Supabase: {e}")
        
        # Try a simple query
        try:
            print("Trying to list tables...")
            response = supabase.table('pg_tables').select('*').limit(5).execute()
            print(f"Tables: {response}")
        except Exception as e:
            print(f"Error listing tables: {e}")
            
            # Try to create a test table
            try:
                print("Trying to create a test table...")
                # Use SQL to create a test table
                response = supabase.rpc('create_test_table').execute()
                print(f"Create table response: {response}")
            except Exception as e:
                print(f"Error creating test table: {e}")

if __name__ == "__main__":
    test_connection()
