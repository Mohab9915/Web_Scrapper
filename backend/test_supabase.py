"""
Test script to verify Supabase connection.
"""
import os
from dotenv import load_dotenv
from supabase import create_client

def test_supabase_connection():
    """Test the Supabase connection."""
    try:
        load_dotenv()
        
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        print(f"Connecting to Supabase at: {supabase_url}")
        
        if not supabase_url or not supabase_key:
            print("Error: SUPABASE_URL or SUPABASE_KEY not found in environment variables")
            return False
            
        # Try to create a client and make a simple query
        supabase = create_client(supabase_url, supabase_key)
        
        # Test a simple query (list tables or get user count)
        try:
            # This is a simple query that should work if the connection is valid
            response = supabase.table('projects').select('*').limit(1).execute()
            print("Successfully connected to Supabase!")
            print(f"Found {len(response.data)} projects in the database.")
            return True
        except Exception as e:
            print(f"Error querying Supabase: {str(e)}")
            return False
            
    except Exception as e:
        print(f"Error connecting to Supabase: {str(e)}")
        return False

if __name__ == "__main__":
    test_supabase_connection()
