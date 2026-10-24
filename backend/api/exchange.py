"""
Token exchange quote signing endpoints for MONY.
"""

from __future__ import annotations

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

import main

logger = logging.getLogger(__name__)

router = APIRouter(tags=["exchange"])


class QuoteRequest(BaseModel):
    user_address: str = Field(..., description="User wallet address")
    token_in: str = Field(..., description="Address of token being paid, or 0x0 for MON")
    token_out: str = Field(..., description="Address of token being received, or 0x0 for MON")
    amount_in: str = Field(..., description="Amount of tokenIn in atomic units")


class QuoteResponse(BaseModel):
    user: str
    token_in: str
    token_out: str
    amount_in: str
    amount_out: str
    nonce: int
    expiry: int
    signature: str


@router.post("/exchange/quote", response_model=QuoteResponse)
async def create_exchange_quote(req: QuoteRequest) -> QuoteResponse:
    if main.quote_signer is None:
        raise HTTPException(status_code=503, detail="Exchange quote signer not initialized")

    try:
        amt_in_int = int(req.amount_in)
    except ValueError:
        raise HTTPException(status_code=400, detail="amount_in must be an integer string")

    if amt_in_int <= 0:
        raise HTTPException(status_code=400, detail="amount_in must be greater than zero")

    # Estimate amount_out based on token pair:
    # If 1:1 stable or demo rate, calculate fair quote
    # For demo mock tokens (mUSDC 6 dec, mDAI 18 dec, mWETH 18 dec, mWBTC 8 dec):
    # If same decimals, approximately 1:1 or based on DEMO_INR_PER_MON
    # Standard demo logic:
    # MON has 18 decimals. If swapping MON (18 dec) for mUSDC (6 dec):
    # 1 MON = $100 -> 100 * 1e6 mUSDC
    amt_out_int = amt_in_int  # default 1:1 if equivalent
    if req.token_in == "0x0000000000000000000000000000000000000000" and req.token_out != "0x0000000000000000000000000000000000000000":
        # MON -> mUSDC (18 dec -> 6 dec at $100/MON demo rate)
        # 1e18 MON -> 100 * 1e6 mUSDC => amt_out = amt_in * 100 / 1e12
        amt_out_int = max(1, (amt_in_int * 100) // (10**12))
    elif req.token_in != "0x0000000000000000000000000000000000000000" and req.token_out == "0x0000000000000000000000000000000000000000":
        # mUSDC -> MON (6 dec -> 18 dec)
        # 100 * 1e6 mUSDC -> 1e18 MON => amt_out = (amt_in * 1e12) // 100
        amt_out_int = max(1, (amt_in_int * (10**12)) // 100)

    signed = main.quote_signer.sign_quote(
        user_address=req.user_address,
        token_in=req.token_in,
        token_out=req.token_out,
        amount_in=amt_in_int,
        amount_out=amt_out_int,
        expiry_offset_seconds=60,
    )

    return QuoteResponse(
        user=signed["user"],
        token_in=signed["tokenIn"],
        token_out=signed["tokenOut"],
        amount_in=signed["amountIn"],
        amount_out=signed["amountOut"],
        nonce=signed["nonce"],
        expiry=signed["expiry"],
        signature=signed["signature"],
    )
