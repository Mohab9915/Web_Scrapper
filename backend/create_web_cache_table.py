#!/usr/bin/env python3
"""
Script to create the web_cache table in the database.
"""
import os
from dotenv import load_dotenv
import httpx
import asyncio

# Load environment variables
load_dotenv()

# Get Supabase credentials from environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Read the SQL script
with open("sql/web_cache_table.sql", "r") as f:
    sql_script = f.read()

async def create_web_cache_table():
    """Create the web_cache table in the database."""
    print("Creating web_cache table...")
    
    # Execute the SQL script using Supabase REST API
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{SUPABASE_URL}/rest/v1/rpc/execute_sql",
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "query": sql_script
            }
        )
        
        if response.status_code == 200:
            print("Web cache table created successfully!")
        else:
            print(f"Error creating web cache table: {response.status_code} - {response.text}")

if __name__ == "__main__":
    asyncio.run(create_web_cache_table())
