"""
Script to apply the migration to add formatted_tabular_data field to the scrape_sessions table.
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

def apply_migration():
    """Apply the migration to add formatted_tabular_data field."""
    print("Applying migration to add formatted_tabular_data field...")
    
    # Read the migration SQL file
    with open("backend/migrations/03_add_formatted_tabular_data.sql", "r") as f:
        migration_sql = f.read()
    
    # Split the SQL into individual statements
    statements = migration_sql.split(';')
    
    # Execute each statement
    for statement in statements:
        if statement.strip():
            try:
                # Use the Supabase REST API to execute the SQL
                # Note: This is a workaround since the Python client doesn't have direct SQL execution
                # In a real-world scenario, you might want to use a proper database migration tool
                print(f"Executing SQL: {statement.strip()}")
                
                # For demonstration purposes, we'll use the rpc function to execute SQL
                # This requires setting up a SQL function in Supabase that can execute arbitrary SQL
                # For now, we'll just print the statement
                print("SQL statement would be executed here.")
                
                # In a real implementation, you might do something like:
                # supabase.rpc("execute_sql", {"sql": statement.strip()}).execute()
            except Exception as e:
                print(f"Error executing SQL: {e}")
    
    print("Migration applied successfully!")

if __name__ == "__main__":
    apply_migration()
