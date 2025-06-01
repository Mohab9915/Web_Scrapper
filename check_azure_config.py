#!/usr/bin/env python3
"""
Check and validate Azure OpenAI configuration.
"""
import os
import sys
import asyncio
import httpx
from urllib.parse import urlparse

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

async def check_azure_config():
    """Check Azure OpenAI configuration"""
    print("🔍 CHECKING AZURE OPENAI CONFIGURATION")
    print("=" * 60)
    
    # Check environment variables
    api_key = os.getenv('AZURE_OPENAI_API_KEY')
    endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
    
    print(f"AZURE_OPENAI_API_KEY: {'✅ Set' if api_key else '❌ Not set'}")
    print(f"AZURE_OPENAI_ENDPOINT: {'✅ Set' if endpoint else '❌ Not set'}")
    
    if api_key:
        print(f"API Key length: {len(api_key)} characters")
        print(f"API Key preview: {api_key[:8]}...{api_key[-4:] if len(api_key) > 12 else ''}")
    
    if endpoint:
        print(f"Endpoint: {endpoint}")
        
        # Validate endpoint format
        try:
            parsed = urlparse(endpoint)
            if parsed.scheme in ['http', 'https'] and parsed.netloc:
                print("✅ Endpoint format is valid")
                
                # Test connectivity
                print("\n🔗 Testing endpoint connectivity...")
                try:
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        # Try to reach the endpoint (this will likely return 404 but confirms connectivity)
                        response = await client.get(endpoint)
                        print(f"✅ Endpoint is reachable (Status: {response.status_code})")
                except httpx.TimeoutException:
                    print("❌ Endpoint timeout - check network connectivity")
                except httpx.ConnectError:
                    print("❌ Cannot connect to endpoint - check URL")
                except Exception as e:
                    print(f"⚠️  Connection test result: {e}")
                    
            else:
                print("❌ Invalid endpoint format - must include http:// or https://")
                
        except Exception as e:
            print(f"❌ Error parsing endpoint: {e}")
    
    # Check if we can import Azure OpenAI client
    print("\n📦 Checking Azure OpenAI client availability...")
    try:
        from openai import AzureOpenAI
        print("✅ Azure OpenAI client is available")
        
        if api_key and endpoint:
            print("\n🧪 Testing Azure OpenAI client initialization...")
            try:
                client = AzureOpenAI(
                    api_key=api_key,
                    api_version="2024-05-01-preview",
                    azure_endpoint=endpoint
                )
                print("✅ Azure OpenAI client initialized successfully")
                
                # Test a simple embedding request
                print("\n🧪 Testing embeddings API...")
                try:
                    response = await asyncio.to_thread(
                        client.embeddings.create,
                        input="test",
                        model="text-embedding-ada-002"
                    )
                    print("✅ Embeddings API is working")
                    print(f"Embedding dimensions: {len(response.data[0].embedding)}")
                except Exception as e:
                    print(f"❌ Embeddings API test failed: {e}")
                
                # Test chat completions
                print("\n🧪 Testing chat completions API...")
                try:
                    response = await asyncio.to_thread(
                        client.chat.completions.create,
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": "Hello, this is a test."}],
                        max_tokens=10
                    )
                    print("✅ Chat completions API is working")
                    print(f"Response: {response.choices[0].message.content}")
                except Exception as e:
                    print(f"❌ Chat completions API test failed: {e}")
                    
            except Exception as e:
                print(f"❌ Azure OpenAI client initialization failed: {e}")
                
    except ImportError:
        print("❌ Azure OpenAI client not available - check installation")
    
    # Check backend configuration
    print("\n⚙️  Checking backend configuration...")
    try:
        from app.database import get_supabase_client
        supabase = get_supabase_client()
        print("✅ Supabase client is working")
        
        # Check if there are any projects with Azure credentials stored
        projects = supabase.table("projects").select("*").limit(5).execute()
        print(f"✅ Found {len(projects.data)} projects in database")
        
    except Exception as e:
        print(f"❌ Backend configuration issue: {e}")
    
    print("\n📋 CONFIGURATION SUMMARY:")
    print("=" * 40)
    
    if api_key and endpoint:
        print("✅ Azure OpenAI credentials are configured")
        print("✅ Ready for RAG operations")
    else:
        print("❌ Azure OpenAI credentials are missing")
        print("📝 To fix this, set the following environment variables:")
        print("   export AZURE_OPENAI_API_KEY='your-api-key'")
        print("   export AZURE_OPENAI_ENDPOINT='https://your-resource.openai.azure.com/'")
        print("\n   Or configure them through the UI settings interface")

def check_env_file():
    """Check if .env file exists and contains Azure config"""
    print("\n📄 Checking .env file...")
    
    env_files = ['.env', 'backend/.env', '.env.local']
    
    for env_file in env_files:
        if os.path.exists(env_file):
            print(f"✅ Found {env_file}")
            try:
                with open(env_file, 'r') as f:
                    content = f.read()
                    
                has_azure_key = 'AZURE_OPENAI_API_KEY' in content
                has_azure_endpoint = 'AZURE_OPENAI_ENDPOINT' in content
                
                print(f"   AZURE_OPENAI_API_KEY: {'✅ Present' if has_azure_key else '❌ Missing'}")
                print(f"   AZURE_OPENAI_ENDPOINT: {'✅ Present' if has_azure_endpoint else '❌ Missing'}")
                
                if not has_azure_key or not has_azure_endpoint:
                    print(f"\n📝 To add Azure config to {env_file}:")
                    print("   AZURE_OPENAI_API_KEY=your-api-key-here")
                    print("   AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/")
                    
            except Exception as e:
                print(f"❌ Error reading {env_file}: {e}")
        else:
            print(f"❌ {env_file} not found")

async def main():
    """Main function"""
    await check_azure_config()
    check_env_file()

if __name__ == "__main__":
    asyncio.run(main())
