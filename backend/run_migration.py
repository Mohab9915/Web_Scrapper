"""
Script to run the migration to create the project_urls table.
"""
import os
from supabase import create_client, Client

# Get Supabase credentials from environment variables
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://slkzwhpfeauezoojlvou.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNsa3p3aHBmZWF1ZXpvb2psdm91Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MTU5NTM2NzcsImV4cCI6MjAzMTUyOTY3N30.Nh83ebqzf1iGHTaFbK8MQK8nZ1lXNLxuQSFDxRGwenc")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Read the migration SQL file
with open("migrations/create_project_urls_table.sql", "r") as f:
    migration_sql = f.read()

# Execute the migration
try:
    # Use the rpc function to execute raw SQL
    response = supabase.rpc(
        "exec_sql", 
        {"sql_query": migration_sql}
    ).execute()
    
    print("Migration executed successfully!")
    print(response)
except Exception as e:
    print(f"Error executing migration: {e}")
