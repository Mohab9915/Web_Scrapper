"""
Script to run the backend server.
"""
import os
import sys
import uvicorn

# Add the backend directory to the path
sys.path.append(os.path.abspath("backend"))

if __name__ == "__main__":
    print("Starting backend server...")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
