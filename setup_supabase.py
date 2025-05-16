"""
Script to set up the Supabase database schema for the Interactive Agentic Web Scraper & RAG System.
"""
import os
import httpx
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase credentials
SUPABASE_URL = "https://slkzwhpfeauezoojlvou.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNsa3p3aHBmZWF1ZXpvb2psdm91Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDcyMTQ0NTEsImV4cCI6MjA2Mjc5MDQ1MX0.uLsJt6GijTe_2MJ0Ckoux9wQrp-Kr6mR43wXPrCYYDQ"

# Read the SQL migration file
with open("backend/migrations/01_initial_schema.sql", "r") as f:
    sql_migration = f.read()

async def execute_sql():
    """Execute the SQL migration on Supabase."""
    print("Setting up Supabase database schema...")
    
    # Split the SQL into individual statements
    sql_statements = sql_migration.split(';')
    
    async with httpx.AsyncClient() as client:
        for statement in sql_statements:
            # Skip empty statements
            if not statement.strip():
                continue
                
            # Add semicolon back
            statement = statement.strip() + ';'
            
            print(f"Executing SQL statement: {statement[:50]}...")
            
            # Execute the SQL statement
            response = await client.post(
                f"{SUPABASE_URL}/rest/v1/rpc/pgexecute",
                headers={
                    "apikey": SUPABASE_KEY,
                    "Authorization": f"Bearer {SUPABASE_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "query": statement
                }
            )
            
            if response.status_code != 200:
                print(f"Error executing SQL: {response.text}")
                return
            
            print("SQL statement executed successfully.")
    
    print("Database schema setup complete!")

if __name__ == "__main__":
    asyncio.run(execute_sql())
