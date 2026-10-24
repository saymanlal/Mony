import pytest
from httpx import AsyncClient, ASGITransport
import main

@pytest.mark.asyncio
async def test_convert_endpoint():
    async with AsyncClient(transport=ASGITransport(app=main.app), base_url="http://test") as client:
        # Before lifespan runs, test rate service fallback
        if main.rate_service is None:
            from rates import RateService
            main.rate_service = RateService()
        response = await client.get("/v1/convert?from=INR&to=MON&amount=8500")
        assert response.status_code == 200
        data = response.json()
        assert data["from"] == "INR"
        assert data["to"] == "MON"
        assert data["amount"] == 8500.0
        assert data["result"] > 0

@pytest.mark.asyncio
async def test_fiat_rates_endpoint():
    async with AsyncClient(transport=ASGITransport(app=main.app), base_url="http://test") as client:
        if main.rate_service is None:
            from rates import RateService
            main.rate_service = RateService()
        response = await client.get("/v1/rates/fiat")
        assert response.status_code == 200
        data = response.json()
        assert "rates" in data
        assert "INR" in data["rates"]
