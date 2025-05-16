"""
Test if we can import the app.
"""
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.abspath("backend"))

try:
    print("Trying to import app.main...")
    from app.main import app
    print("Successfully imported app.main!")
except Exception as e:
    print(f"Error importing app.main: {e}")
    
    # Try to import each module separately
    try:
        print("\nTrying to import app.config...")
        from app.config import settings
        print(f"Successfully imported app.config! CORS_ORIGINS: {settings.CORS_ORIGINS}")
    except Exception as e:
        print(f"Error importing app.config: {e}")
    
    try:
        print("\nTrying to import app.api.projects...")
        from app.api import projects
        print("Successfully imported app.api.projects!")
    except Exception as e:
        print(f"Error importing app.api.projects: {e}")
    
    try:
        print("\nTrying to import app.api.scraping...")
        from app.api import scraping
        print("Successfully imported app.api.scraping!")
    except Exception as e:
        print(f"Error importing app.api.scraping: {e}")
    
    try:
        print("\nTrying to import app.api.rag...")
        from app.api import rag
        print("Successfully imported app.api.rag!")
    except Exception as e:
        print(f"Error importing app.api.rag: {e}")
