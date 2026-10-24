"""
Exchange rates API endpoints and Server-Sent Events (SSE) stream for MONY.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, AsyncGenerator

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

import main

logger = logging.getLogger(__name__)

router = APIRouter(tags=["rates"])


@router.get("/rates/fiat")
async def get_fiat_rates():
    if main.rate_service is None:
        raise HTTPException(status_code=503, detail="Rate service not initialized")
    return await main.rate_service.get_fiat_rates()


@router.get("/rates/token")
async def get_token_rate(
    platform: str = Query(..., description="EVM platform name (e.g. ethereum, polygon-pos)"),
    contract_address: str = Query(..., description="EVM token contract address"),
):
    if main.rate_service is None:
        raise HTTPException(status_code=503, detail="Rate service not initialized")
    try:
        return await main.rate_service.get_token_rate(platform, contract_address)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch token rate: {str(e)}")


@router.get("/rates/search")
async def search_tokens(q: str = Query(..., min_length=1, description="Token name or ticker")):
    if main.rate_service is None:
        raise HTTPException(status_code=503, detail="Rate service not initialized")
    return await main.rate_service.search_tokens(q)


@router.get("/convert")
async def convert_currency(
    from_currency: str = Query(..., alias="from", description="Source currency (INR or MON)"),
    to_currency: str = Query(..., alias="to", description="Target currency (INR or MON)"),
    amount: float = Query(..., gt=0, description="Amount to convert"),
):
    if main.rate_service is None:
        raise HTTPException(status_code=503, detail="Rate service not initialized")
    try:
        return await main.rate_service.convert(from_currency, to_currency, amount)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/stream/rates")
async def stream_rates():
    """
    Server-Sent Events endpoint pushing INR/MON rates every 15 seconds.
    """
    async def event_generator() -> AsyncGenerator[str, None]:
        while True:
            try:
                if main.rate_service is not None:
                    rate_data = await main.rate_service.get_mon_inr_rate()
                    payload = json.dumps(rate_data)
                    yield f"event: rate_tick\ndata: {payload}\n\n"
            except Exception as e:
                logger.error(f"Error in rates SSE stream: {e}")
                err_payload = json.dumps({"error": str(e), "stale": True})
                yield f"event: error\ndata: {err_payload}\n\n"

            await asyncio.sleep(15)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
