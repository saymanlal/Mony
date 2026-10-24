"""
Invoice generation and record endpoints for MONY.
"""

from __future__ import annotations

import logging
import time
import uuid
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

import db

logger = logging.getLogger(__name__)

router = APIRouter(tags=["invoices"])


class CreateInvoiceRequest(BaseModel):
    user_address: str
    recipient_address: Optional[str] = None
    transaction_type: str = "deposit"  # deposit | transfer | swap
    amount_mon: float
    amount_inr: float
    rate_used: float
    tx_hash: Optional[str] = None
    description: Optional[str] = None


class InvoiceResponse(BaseModel):
    id: str
    invoice_number: str
    user_address: str
    recipient_address: Optional[str]
    transaction_type: str
    amount_mon: float
    amount_inr: float
    rate_used: float
    tx_hash: Optional[str]
    explorer_url: Optional[str]
    created_at_ts: int
    description: Optional[str]


@router.post("/invoices", response_model=InvoiceResponse)
async def create_invoice(req: CreateInvoiceRequest) -> InvoiceResponse:
    invoice_id = str(uuid.uuid4())
    ts = int(time.time())
    invoice_number = f"INV-{ts}-{uuid.uuid4().hex[:6].upper()}"
    explorer_url = f"https://testnet.monadexplorer.com/tx/{req.tx_hash}" if req.tx_hash else None

    query = """
    INSERT INTO invoices (id, user_address, invoice_number, amount_inr, amount_mon, recipient_name, description, status, pdf_data)
    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9::jsonb)
    """
    pdf_data = {
        "invoice_number": invoice_number,
        "tx_type": req.transaction_type,
        "rate": req.rate_used,
        "tx_hash": req.tx_hash,
        "explorer_url": explorer_url,
    }
    try:
        import json
        await db.execute(
            query,
            uuid.UUID(invoice_id),
            req.user_address,
            invoice_number,
            req.amount_inr,
            req.amount_mon,
            req.recipient_address,
            req.description,
            "issued",
            json.dumps(pdf_data),
        )
    except Exception as e:
        logger.warning(f"Could not persist invoice in database: {e}")

    return InvoiceResponse(
        id=invoice_id,
        invoice_number=invoice_number,
        user_address=req.user_address,
        recipient_address=req.recipient_address,
        transaction_type=req.transaction_type,
        amount_mon=req.amount_mon,
        amount_inr=req.amount_inr,
        rate_used=req.rate_used,
        tx_hash=req.tx_hash,
        explorer_url=explorer_url,
        created_at_ts=ts,
        description=req.description,
    )
