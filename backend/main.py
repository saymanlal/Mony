"""
MONY backend - FastAPI application entrypoint.
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic_settings import BaseSettings, SettingsConfigDict

import db
from rates import RateService
from signer import ExchangeQuoteSigner, VoucherSigner
from relayer import Relayer
from engine.verifier import BanknoteVerifier

# ------------------------------------------------------------------ #
# Settings                                                             #
# ------------------------------------------------------------------ #


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = ""
    monad_rpc_url: str = "https://testnet-rpc.monad.xyz"
    chain_id: int = 10143
    treasury_address: str = "0x0000000000000000000000000000000000000000"
    exchange_address: str = "0x0000000000000000000000000000000000000000"
    verifier_signer_key: str = "0x0000000000000000000000000000000000000000000000000000000000000001"
    relayer_key: str = "0x0000000000000000000000000000000000000000000000000000000000000002"
    quote_signer_key: str = "0x0000000000000000000000000000000000000000000000000000000000000003"
    challenge_secret: str = "a" * 64
    server_salt: str = "b" * 32
    demo_inr_per_mon: float = 8500.0
    allowed_origins: str = "http://localhost:8081,http://localhost:3000"
    coingecko_api_key: str = ""
    rate_cache_ttl_seconds: float = 60.0
    rate_stale_ttl_seconds: float = 300.0


settings = Settings()

# ------------------------------------------------------------------ #
# Logging                                                              #
# ------------------------------------------------------------------ #

logging.basicConfig(
    level=logging.INFO,
    format='{"time":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","msg":%(message)s}',
)
logger = logging.getLogger("mony.main")

# ------------------------------------------------------------------ #
# Singleton service objects (populated during lifespan)               #
# ------------------------------------------------------------------ #

rate_service: RateService | None = None
voucher_signer: VoucherSigner | None = None
quote_signer: ExchangeQuoteSigner | None = None
relayer: Relayer | None = None
banknote_verifier: BanknoteVerifier | None = None


# ------------------------------------------------------------------ #
# Rate limiting (in-memory, per-IP sliding window)                    #
# ------------------------------------------------------------------ #

import time
import collections

_rate_limit_windows: dict[str, list[float]] = collections.defaultdict(list)
RATE_LIMIT_WINDOW_SECONDS = 60
RATE_LIMIT_MAX_REQUESTS = 120  # per IP per window


def _check_rate_limit(ip: str, max_req: int = RATE_LIMIT_MAX_REQUESTS) -> bool:
    """Return True if the IP is within the rate limit, False if exceeded."""
    now = time.monotonic()
    window = _rate_limit_windows[ip]
    cutoff = now - RATE_LIMIT_WINDOW_SECONDS
    while window and window[0] < cutoff:
        window.pop(0)
    if len(window) >= max_req:
        return False
    window.append(now)
    return True


# ------------------------------------------------------------------ #
# Lifespan                                                             #
# ------------------------------------------------------------------ #


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    global rate_service, voucher_signer, quote_signer, relayer, banknote_verifier

    # Database
    if settings.database_url:
        await db.init_pool(settings.database_url)
    else:
        logger.warning("DATABASE_URL not set; DB operations will fail at runtime")

    # Rate service
    rate_service = RateService(
        coingecko_api_key=settings.coingecko_api_key,
        demo_inr_per_mon=settings.demo_inr_per_mon,
        cache_ttl_seconds=settings.rate_cache_ttl_seconds,
        stale_ttl_seconds=settings.rate_stale_ttl_seconds,
    )
    await rate_service.start()

    # EIP-712 signers
    voucher_signer = VoucherSigner(
        private_key=settings.verifier_signer_key,
        treasury_address=settings.treasury_address,
        chain_id=settings.chain_id,
    )
    quote_signer = ExchangeQuoteSigner(
        private_key=settings.quote_signer_key,
        exchange_address=settings.exchange_address,
        chain_id=settings.chain_id,
    )

    # Relayer
    relayer = Relayer(
        rpc_url=settings.monad_rpc_url,
        chain_id=settings.chain_id,
        treasury_address=settings.treasury_address,
        relayer_private_key=settings.relayer_key,
    )

    # Engine verifier
    banknote_verifier = BanknoteVerifier(
        verifier_private_key=settings.verifier_signer_key,
        treasury_address=settings.treasury_address,
        challenge_secret=settings.challenge_secret,
        chain_id=settings.chain_id,
    )

    logger.info('"MONY backend started"')
    yield

    # Shutdown
    await rate_service.stop()
    await db.close_pool()
    logger.info('"MONY backend stopped"')


# ------------------------------------------------------------------ #
# App                                                                  #
# ------------------------------------------------------------------ #

app = FastAPI(
    title="MONY Backend API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS
allowed_origins = [o.strip() for o in settings.allowed_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Rate limit middleware
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    ip = request.client.host if request.client else "unknown"
    if not _check_rate_limit(ip):
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded. Please slow down."},
        )
    return await call_next(request)


# ------------------------------------------------------------------ #
# Routers                                                              #
# ------------------------------------------------------------------ #

from api.scan import router as scan_router
from api.deposit import router as deposit_router
from api.rates import router as rates_router
from api.exchange import router as exchange_router
from api.analytics import router as analytics_router
from api.invoices import router as invoices_router
from api.health import router as health_router

app.include_router(scan_router, prefix="/v1")
app.include_router(deposit_router, prefix="/v1")
app.include_router(rates_router, prefix="/v1")
app.include_router(exchange_router, prefix="/v1")
app.include_router(analytics_router, prefix="/v1")
app.include_router(invoices_router, prefix="/v1")
app.include_router(health_router, prefix="/v1")
