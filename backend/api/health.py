"""
Health check endpoint for MONY backend.
"""

from __future__ import annotations

import time
from fastapi import APIRouter
from pydantic import BaseModel

import db

router = APIRouter(tags=["health"])

_START_TIME = time.time()


class HealthResponse(BaseModel):
    status: str
    uptime_seconds: float
    database: str
    chain_id: int
    version: str


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    db_status = "connected" if db._pool is not None else "disconnected"
    return HealthResponse(
        status="ok",
        uptime_seconds=round(time.time() - _START_TIME, 2),
        database=db_status,
        chain_id=10143,
        version="1.0.0",
    )
