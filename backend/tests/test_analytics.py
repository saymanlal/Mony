import pytest
from httpx import AsyncClient, ASGITransport
import main

@pytest.mark.asyncio
async def test_analytics_summary_endpoint():
    async with AsyncClient(transport=ASGITransport(app=main.app), base_url="http://test") as client:
        response = await client.get("/v1/analytics/summary?user_address=0x1111111111111111111111111111111111111111")
        assert response.status_code == 200
        data = response.json()
        assert data["user_address"] == "0x1111111111111111111111111111111111111111"
        assert "savings_rate_pct" in data
        assert "forecast_7d" in data
        assert "insights" in data
        assert len(data["insights"]) > 0
