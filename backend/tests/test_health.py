"""
Test the health check endpoint.
"""
import httpx # Changed from TestClient
import pytest # Added for asyncio marker
from httpx import ASGITransport # Import ASGITransport

from app.main import app

# client = TestClient(app) # Original instantiation commented out

@pytest.mark.asyncio # Test must be async now
async def test_health_check():
    """Test the health check endpoint."""
    # Using explicit ASGITransport
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
