"""
Deposit release and quote endpoints for MONY.
"""

from __future__ import annotations

import logging
import time
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

import db
import main

logger = logging.getLogger(__name__)

router = APIRouter(tags=["deposit"])


class DepositQuoteResponse(BaseModel):
    denomination_inr: int
    user_address: str
    inr_per_mon: float
    amount_mon: float
    amount_wei: str
    locked_until_ts: int
    is_demo_rate: bool


class ReleaseDepositRequest(BaseModel):
    user_address: str
    mode: str = "automated"  # automated | manual
    voucher: dict
    deposit_intent: Optional[dict] = None
    user_signature: Optional[str] = None


class ReleaseDepositResponse(BaseModel):
    status: str
    tx_hash: Optional[str] = None
    user_address: str
    amount_mon: float
    amount_wei: str
    mode: str
    message: str


@router.get("/quote/deposit", response_model=DepositQuoteResponse)
async def get_deposit_quote(
    denomination: int = Query(..., description="Banknote denomination in INR (10, 20, 50, 100, 200, 500)"),
    user_address: str = Query(..., description="User EVM wallet address"),
) -> DepositQuoteResponse:
    if denomination not in [10, 20, 50, 100, 200, 500]:
        raise HTTPException(status_code=400, detail="Unsupported denomination")

    rate_data = {"inr_per_mon": main.settings.demo_inr_per_mon, "is_demo": True}
    if main.rate_service is not None:
        try:
            rate_data = await main.rate_service.get_inr_per_mon()
        except Exception as e:
            logger.warning(f"Failed to fetch live rate, using demo fallback: {e}")

    inr_per_mon = rate_data.get("inr_per_mon", main.settings.demo_inr_per_mon)
    amount_mon = round(denomination / inr_per_mon, 6)
    amount_wei = str(int(amount_mon * 10**18))
    locked_until = int(time.time()) + 30

    return DepositQuoteResponse(
        denomination_inr=denomination,
        user_address=user_address,
        inr_per_mon=inr_per_mon,
        amount_mon=amount_mon,
        amount_wei=amount_wei,
        locked_until_ts=locked_until,
        is_demo_rate=rate_data.get("is_demo", True),
    )


@router.post("/deposit/release", response_model=ReleaseDepositResponse)
async def release_deposit(payload: ReleaseDepositRequest) -> ReleaseDepositResponse:
    voucher = payload.voucher
    user_addr = payload.user_address
    mode = payload.mode.lower()

    if not voucher:
        raise HTTPException(status_code=400, detail="Missing verification voucher")

    amount_wei = str(voucher.get("amount_wei", "0"))
    amount_mon = float(voucher.get("amount_mon", 0.0))
    denomination = int(voucher.get("denomination_inr", 0))

    if main.relayer is None:
        raise HTTPException(status_code=503, detail="Relayer service is not initialized")

    try:
        if mode == "manual":
            if not payload.deposit_intent or not payload.user_signature:
                raise HTTPException(
                    status_code=400,
                    detail="Manual mode requires deposit_intent and user_signature",
                )
            tx_hash = await main.relayer.submit_redeem_for(
                voucher=voucher,
                verifier_signature=voucher.get("signature", ""),
                deposit_intent=payload.deposit_intent,
                user_signature=payload.user_signature,
            )
        else:
            tx_hash = await main.relayer.submit_redeem(
                voucher=voucher,
                verifier_signature=voucher.get("signature", ""),
            )

        # Record deposit in DB
        await db.record_deposit(
            scan_id=None,
            user_address=user_addr,
            mode=mode,
            tx_hash=tx_hash,
            status="confirmed",
            amount_wei=amount_wei,
            amount_mon=amount_mon,
            denomination=denomination,
        )

        return ReleaseDepositResponse(
            status="confirmed",
            tx_hash=tx_hash,
            user_address=user_addr,
            amount_mon=amount_mon,
            amount_wei=amount_wei,
            mode=mode,
            message="MON successfully dispatched to wallet on Monad testnet",
        )
    except Exception as e:
        logger.error(f"Deposit release transaction failed: {e}")
        await db.record_deposit(
            scan_id=None,
            user_address=user_addr,
            mode=mode,
            tx_hash=None,
            status="failed",
            amount_wei=amount_wei,
            amount_mon=amount_mon,
            denomination=denomination,
            error_message=str(e),
        )
        raise HTTPException(status_code=500, detail=f"Transaction release failed: {str(e)}")
