import pytest
from httpx import AsyncClient, ASGITransport
import main
from engine.verifier import BanknoteVerifier

@pytest.mark.asyncio
async def test_challenge_endpoint():
    if main.banknote_verifier is None:
        main.banknote_verifier = BanknoteVerifier(
            verifier_private_key="0x" + "1" * 64,
            treasury_address="0x" + "2" * 40,
            challenge_secret="secret" * 8,
        )
    async with AsyncClient(transport=ASGITransport(app=main.app), base_url="http://test") as client:
        response = await client.post("/v1/scan/challenge")
        assert response.status_code == 200
        data = response.json()
        assert "nonce" in data
        assert "hmac_signature" in data
        assert "session_id" in data
