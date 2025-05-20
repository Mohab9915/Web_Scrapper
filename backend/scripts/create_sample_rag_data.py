"""
Script to create sample RAG data for a project.
"""
import asyncio
import sys
import os
from uuid import UUID
import httpx

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import supabase
from app.services.rag_service import generate_embeddings, chunk_text

async def create_sample_rag_data(project_id: str, session_id: str):
    """
    Create sample RAG data for a project.
    
    Args:
        project_id (str): Project ID
        session_id (str): Session ID
    """
    try:
        # Check if project exists
        project_response = supabase.table("projects").select("*").eq("id", project_id).single().execute()
        if not project_response.data:
            print(f"Project {project_id} not found")
            return
        
        print(f"Project {project_id} found: {project_response.data['name']}")
        
        # Check if session exists
        session_response = supabase.table("scrape_sessions").select("*").eq("id", session_id).single().execute()
        if not session_response.data:
            print(f"Session {session_id} not found")
            return
        
        print(f"Session {session_id} found: {session_response.data['url']}")
        
        # Get the URL from the session
        url = session_response.data['url']
        unique_scrape_identifier = session_response.data['unique_scrape_identifier']
        
        # Fetch the content from the URL
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            if response.status_code != 200:
                print(f"Failed to fetch content from {url}")
                return
            
            html_content = response.text
            print(f"Fetched {len(html_content)} characters from {url}")
            
            # Convert HTML to markdown (simple version)
            markdown_content = f"""
# Content from {url}

This is a sample markdown document created for RAG testing.

## E-commerce Website

This website contains various products including:

- Laptops
- Phones
- Monitors
- Tablets

### Product Details

Products have the following attributes:
- Name
- Price
- Description
- Rating
- Reviews

### Sample Products

1. Lenovo IdeaPad
   - Price: $399.99
   - Rating: 4.5/5
   - Description: A powerful laptop for everyday use

2. Samsung Galaxy S21
   - Price: $799.99
   - Rating: 4.8/5
   - Description: Latest smartphone with advanced camera

3. Dell UltraSharp Monitor
   - Price: $349.99
   - Rating: 4.3/5
   - Description: 27-inch 4K monitor for professionals

4. Apple iPad Pro
   - Price: $999.99
   - Rating: 4.9/5
   - Description: High-performance tablet with M1 chip
"""
            
            # Insert into markdowns table
            markdown_response = supabase.table("markdowns").insert({
                "unique_name": unique_scrape_identifier,
                "url": url,
                "markdown": markdown_content
            }).execute()
            
            if not markdown_response.data:
                print("Failed to insert markdown content")
                return
            
            print("Markdown content inserted successfully")
            
            # Chunk the markdown content
            chunks = await chunk_text(markdown_content)
            print(f"Created {len(chunks)} chunks")
            
            # Azure OpenAI credentials
            azure_credentials = {
                'api_key': 'BuVHZw4d7OmEwH5QIsvw8gsKLyRxNUow4PT1gYg83iukV6JLRVL8JQQJ99BDACHYHv6XJ3w3AAAAACOGR8LC',
                'endpoint': 'https://practicehub3994533910.services.ai.azure.com',
                'deployment_name': 'text-embedding-ada-002'
            }
            
            # Generate embeddings for each chunk
            for i, chunk in enumerate(chunks):
                print(f"Generating embedding for chunk {i+1}/{len(chunks)}")
                embedding = await generate_embeddings(chunk, azure_credentials)
                
                # Insert into embeddings table
                supabase.table("embeddings").insert({
                    "unique_name": unique_scrape_identifier,
                    "chunk_id": i,
                    "content": chunk,
                    "embedding": embedding
                }).execute()
                
                print(f"Embedding {i+1} inserted successfully")
            
            print("All embeddings inserted successfully")
            
            # Update session status
            supabase.table("scrape_sessions").update({
                "status": "rag_ingested"
            }).eq("id", session_id).execute()
            
            print(f"Session {session_id} updated to status 'rag_ingested'")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python create_sample_rag_data.py <project_id> <session_id>")
        sys.exit(1)
    
    project_id = sys.argv[1]
    session_id = sys.argv[2]
    asyncio.run(create_sample_rag_data(project_id, session_id))
