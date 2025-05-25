import os
from supabase import create_client

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://slkzwhpfeauezoojlvou.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNsa3p3aHBmZWF1ZXpvb2psdm91Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MTU5NTM2NzcsImV4cCI6MjAzMTUyOTY3N30.Nh83ebqzf1iGHTaFbK8MQK8nZ1lXNLxuQSFDxRGwenc")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    response = supabase.rpc('exec_sql', {'sql_query': 'UPDATE project_urls SET rag_enabled = FALSE WHERE rag_enabled IS NULL;'}).execute()
    print('Successfully updated rag_enabled column.')
    print(response)
except Exception as e:
    print(f'Error executing SQL query: {e}')