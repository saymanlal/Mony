"""
Database layer for the MONY backend.

Uses asyncpg directly for async Postgres access.
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    import asyncpg  # type: ignore
    ASYNCPG_AVAILABLE = True
except ModuleNotFoundError:
    asyncpg = None  # type: ignore
    ASYNCPG_AVAILABLE = False


_pool: Optional[Any] = None


async def init_pool(database_url: str) -> None:
    global _pool
    if not ASYNCPG_AVAILABLE:
        logger.warning("asyncpg not installed; database operations will fail at runtime")
        return

    dsn = database_url.replace("postgresql+asyncpg://", "postgresql://")
    _pool = await asyncpg.create_pool(
        dsn=dsn,
        min_size=2,
        max_size=10,
        command_timeout=30,
    )
    logger.info("asyncpg connection pool created")


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
        logger.info("asyncpg connection pool closed")


def get_pool() -> Any:
    if _pool is None:
        raise RuntimeError("Database pool is not initialised. Call init_pool() first.")
    return _pool


@asynccontextmanager
async def acquire() -> AsyncGenerator[Any, None]:
    pool = get_pool()
    async with pool.acquire() as conn:
        yield conn


async def fetchrow(query: str, *args: Any) -> Optional[dict]:
    if _pool is None:
        return None
    async with acquire() as conn:
        row = await conn.fetchrow(query, *args)
        return dict(row) if row else None


async def fetch(query: str, *args: Any) -> List[dict]:
    if _pool is None:
        return []
    async with acquire() as conn:
        rows = await conn.fetch(query, *args)
        return [dict(r) for r in rows]


async def execute(query: str, *args: Any) -> str:
    if _pool is None:
        return ""
    async with acquire() as conn:
        return await conn.execute(query, *args)


async def fetchval(query: str, *args: Any) -> Any:
    if _pool is None:
        return None
    async with acquire() as conn:
        return await conn.fetchval(query, *args)


# ------------------------------------------------------------------ #
# Application DB helpers                                               #
# ------------------------------------------------------------------ #

async def get_all_redeemed_note_hashes() -> List[dict]:
    return await fetch("SELECT note_hash, phash, denomination FROM notes")


async def record_scan(
    user_address: str,
    decision: str,
    reason_code: str,
    score: float,
    voucher_data: Optional[Dict[str, Any]] = None,
    breakdown: Optional[Dict[str, Any]] = None,
) -> str:
    scan_id = str(uuid.uuid4())
    session_id = f"sess_{uuid.uuid4().hex[:16]}"
    note_hash = voucher_data.get("note_hash") if voucher_data else None
    denomination = voucher_data.get("denomination_inr") if voucher_data else None
    amount_mon = voucher_data.get("amount_mon") if voucher_data else None
    amount_wei = voucher_data.get("amount_wei") if voucher_data else None
    voucher_json = json.dumps(voucher_data) if voucher_data else None
    layer_scores_json = json.dumps(breakdown) if breakdown else "{}"

    query = """
    INSERT INTO scans (id, session_id, user_address, decision, score, reason_code, layer_scores, note_hash, denomination, amount_mon, amount_wei, voucher_json)
    VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb, $8, $9, $10, $11, $12::jsonb)
    """
    await execute(
        query,
        uuid.UUID(scan_id),
        session_id,
        user_address,
        decision,
        score,
        reason_code,
        layer_scores_json,
        note_hash,
        denomination,
        amount_mon,
        amount_wei,
        voucher_json,
    )

    if decision == "ACCEPT" and note_hash and denomination:
        phash = breakdown.get("layer4", {}).get("phash", "") if breakdown else ""
        await register_note(note_hash, phash, denomination, user_address, scan_id)

    return scan_id


async def register_note(
    note_hash: str,
    phash: str,
    denomination: int,
    user_address: str,
    scan_id: str,
) -> None:
    query = """
    INSERT INTO notes (note_hash, phash, denomination, user_address, scan_id)
    VALUES ($1, $2, $3, $4, $5)
    ON CONFLICT (note_hash) DO NOTHING
    """
    await execute(query, note_hash, phash, denomination, user_address, uuid.UUID(scan_id))


async def record_deposit(
    scan_id: Optional[str],
    user_address: str,
    mode: str,
    tx_hash: Optional[str],
    status: str,
    amount_wei: str,
    amount_mon: float,
    denomination: int,
    error_message: Optional[str] = None,
) -> str:
    deposit_id = str(uuid.uuid4())
    s_uuid = uuid.UUID(scan_id) if scan_id else None
    query = """
    INSERT INTO deposits (id, scan_id, user_address, mode, tx_hash, status, amount_wei, amount_mon, denomination, error_message)
    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
    """
    await execute(
        query,
        uuid.UUID(deposit_id),
        s_uuid,
        user_address,
        mode,
        tx_hash,
        status,
        amount_wei,
        amount_mon,
        denomination,
        error_message,
    )
    return deposit_id


async def get_user_activity(user_address: str, limit: int = 50) -> List[dict]:
    query = """
    SELECT id, user_address, mode, tx_hash, status, amount_mon, denomination, created_at, 'deposit' as activity_type
    FROM deposits
    WHERE LOWER(user_address) = LOWER($1)
    ORDER BY created_at DESC
    LIMIT $2
    """
    return await fetch(query, user_address, limit)
