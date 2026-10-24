import pytest
from httpx import AsyncClient, ASGITransport
import main

@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(transport=ASGITransport(app=main.app), base_url="http://test") as client:
        response = await client.get("/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["chain_id"] == 10143
        assert "uptime_seconds" in data
