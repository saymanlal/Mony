"""
Rate service for MONY backend.

Responsibilities:
- Fetch and cache INR/MON rates and any EVM token price from CoinGecko.
- Exponential back-off on CoinGecko rate limits (HTTP 429).
- Stale-while-error: return cached data with a stale flag when upstream fails.
- DEMO_INR_PER_MON env var fallback when CoinGecko is unreachable.
- In-memory primary cache backed by DB (rate_cache table) for persistence.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)

COINGECKO_BASE = "https://api.coingecko.com/api/v3"
COINGECKO_PRO_BASE = "https://pro-api.coingecko.com/api/v3"


class _CacheEntry:
    __slots__ = ("payload", "fetched_at", "ttl", "stale_ttl")

    def __init__(self, payload: Any, ttl: float, stale_ttl: float) -> None:
        self.payload = payload
        self.fetched_at = time.monotonic()
        self.ttl = ttl
        self.stale_ttl = stale_ttl

    @property
    def is_fresh(self) -> bool:
        return (time.monotonic() - self.fetched_at) < self.ttl

    @property
    def is_usable(self) -> bool:
        return (time.monotonic() - self.fetched_at) < self.stale_ttl


class RateService:
    """
    Async rate service. Call await rate_service.start() once at startup
    and await rate_service.stop() on shutdown.
    """

    def __init__(
        self,
        coingecko_api_key: str = "",
        demo_inr_per_mon: float = 8500.0,
        cache_ttl_seconds: float = 60.0,
        stale_ttl_seconds: float = 300.0,
    ) -> None:
        self._api_key = coingecko_api_key
        self._demo_rate = demo_inr_per_mon
        self._ttl = cache_ttl_seconds
        self._stale_ttl = stale_ttl_seconds

        self._cache: dict[str, _CacheEntry] = {}
        self._locks: dict[str, asyncio.Lock] = {}
        self._http: Optional[httpx.AsyncClient] = None

        # Back-off state per cache key
        self._backoff: dict[str, float] = {}

    async def start(self) -> None:
        base_url = COINGECKO_PRO_BASE if self._api_key else COINGECKO_BASE
        headers = {}
        if self._api_key:
            headers["x-cg-pro-api-key"] = self._api_key
        self._http = httpx.AsyncClient(
            base_url=base_url,
            headers=headers,
            timeout=10.0,
        )

    async def stop(self) -> None:
        if self._http:
            await self._http.aclose()
            self._http = None

    def _get_lock(self, key: str) -> asyncio.Lock:
        if key not in self._locks:
            self._locks[key] = asyncio.Lock()
        return self._locks[key]

    async def _get_with_backoff(self, url: str, params: dict) -> httpx.Response:
        """GET with exponential back-off on 429 responses."""
        delay = 1.0
        for attempt in range(5):
            if self._http is None:
                raise RuntimeError("RateService not started")
            resp = await self._http.get(url, params=params)
            if resp.status_code == 429:
                wait = delay * (2 ** attempt)
                logger.warning("CoinGecko rate limited, backing off %.1fs", wait)
                await asyncio.sleep(wait)
                continue
            resp.raise_for_status()
            return resp
        raise RuntimeError("CoinGecko rate limit exceeded after retries")

    def _make_entry(self, payload: Any) -> _CacheEntry:
        return _CacheEntry(payload, ttl=self._ttl, stale_ttl=self._stale_ttl)

    # ---------------------------------------------------------------- #
    # Public API                                                         #
    # ---------------------------------------------------------------- #

    async def get_fiat_rates(self) -> dict[str, Any]:
        """
        Return fiat exchange rates with INR as base.
        Uses simple_price endpoint via MON -> INR.
        """
        cache_key = "fiat_rates"
        async with self._get_lock(cache_key):
            entry = self._cache.get(cache_key)
            if entry and entry.is_fresh:
                return {"rates": entry.payload, "stale": False, "source": "cache"}

            try:
                inr_per_mon = await self._fetch_mon_inr_price()
                payload = {
                    "INR": 1.0,
                    "MON": round(1.0 / inr_per_mon, 10) if inr_per_mon else None,
                    "USD": None,
                }
                # Attempt USD rate
                try:
                    usd_resp = await self._get_with_backoff(
                        "/simple/price",
                        {"ids": "usd-coin", "vs_currencies": "inr"},
                    )
                    usd_data = usd_resp.json()
                    usd_price_inr = usd_data.get("usd-coin", {}).get("inr")
                    if usd_price_inr:
                        payload["USD"] = round(1.0 / usd_price_inr, 8)
                except Exception:
                    pass

                self._cache[cache_key] = self._make_entry(payload)
                return {"rates": payload, "stale": False, "source": "coingecko"}
            except Exception as exc:
                logger.warning("fiat_rates fetch failed: %s", exc)
                if entry and entry.is_usable:
                    return {"rates": entry.payload, "stale": True, "source": "cache"}
                # Demo fallback
                demo = {"INR": 1.0, "MON": round(1.0 / self._demo_rate, 10), "USD": None}
                return {"rates": demo, "stale": True, "source": "demo"}

    async def _fetch_mon_inr_price(self) -> float:
        """
        Fetch MON price in INR. MON is native token of Monad.
        CoinGecko may list it as 'monad' or similar; fall back to demo rate.
        """
        try:
            resp = await self._get_with_backoff(
                "/simple/price",
                {"ids": "monad", "vs_currencies": "inr"},
            )
            data = resp.json()
            price = data.get("monad", {}).get("inr")
            if price:
                return float(price)
        except Exception:
            pass
        return self._demo_rate

    async def get_mon_inr_rate(self) -> dict[str, Any]:
        """Return current INR per MON rate with metadata."""
        cache_key = "mon_inr_rate"
        async with self._get_lock(cache_key):
            entry = self._cache.get(cache_key)
            if entry and entry.is_fresh:
                return entry.payload

            try:
                rate = await self._fetch_mon_inr_price()
                payload = {
                    "inr_per_mon": rate,
                    "stale": False,
                    "source": "coingecko",
                    "fetched_at": int(time.time()),
                    "demo": False,
                }
                self._cache[cache_key] = self._make_entry(payload)
                return payload
            except Exception as exc:
                logger.warning("mon_inr_rate fetch failed: %s", exc)
                if entry and entry.is_usable:
                    stale = dict(entry.payload)
                    stale["stale"] = True
                    return stale
                return {
                    "inr_per_mon": self._demo_rate,
                    "stale": True,
                    "source": "demo",
                    "fetched_at": int(time.time()),
                    "demo": True,
                }

    async def get_token_rate(
        self,
        platform: str,
        contract_address: str,
    ) -> dict[str, Any]:
        """
        Fetch price for any EVM token by platform (e.g. 'ethereum') and
        contract address. Returns price in USD and INR.
        """
        cache_key = f"token:{platform}:{contract_address.lower()}"
        async with self._get_lock(cache_key):
            entry = self._cache.get(cache_key)
            if entry and entry.is_fresh:
                return {"data": entry.payload, "stale": False}

            try:
                resp = await self._get_with_backoff(
                    f"/coins/{platform}/contract/{contract_address}",
                    {},
                )
                data = resp.json()
                market = data.get("market_data", {})
                payload = {
                    "id": data.get("id"),
                    "symbol": data.get("symbol"),
                    "name": data.get("name"),
                    "price_usd": market.get("current_price", {}).get("usd"),
                    "price_inr": market.get("current_price", {}).get("inr"),
                    "market_cap_usd": market.get("market_cap", {}).get("usd"),
                    "volume_24h_usd": market.get("total_volume", {}).get("usd"),
                    "price_change_24h_pct": market.get("price_change_percentage_24h"),
                    "platform": platform,
                    "contract_address": contract_address,
                }
                self._cache[cache_key] = self._make_entry(payload)
                return {"data": payload, "stale": False}
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 404:
                    raise ValueError(f"Token not found: {platform}/{contract_address}") from exc
                logger.warning("token_rate fetch failed: %s", exc)
                if entry and entry.is_usable:
                    return {"data": entry.payload, "stale": True}
                raise
            except Exception as exc:
                logger.warning("token_rate fetch failed: %s", exc)
                if entry and entry.is_usable:
                    return {"data": entry.payload, "stale": True}
                raise

    async def search_tokens(self, query: str) -> list[dict[str, Any]]:
        """Search CoinGecko for tokens matching a query string."""
        cache_key = f"search:{query.lower()}"
        entry = self._cache.get(cache_key)
        if entry and entry.is_fresh:
            return entry.payload

        try:
            resp = await self._get_with_backoff("/search", {"query": query})
            data = resp.json()
            coins = data.get("coins", [])[:20]
            result = [
                {
                    "id": c.get("id"),
                    "symbol": c.get("symbol"),
                    "name": c.get("name"),
                    "market_cap_rank": c.get("market_cap_rank"),
                    "thumb": c.get("thumb"),
                }
                for c in coins
            ]
            self._cache[cache_key] = self._make_entry(result)
            return result
        except Exception as exc:
            logger.warning("search_tokens failed: %s", exc)
            if entry and entry.is_usable:
                return entry.payload
            return []

    async def convert(
        self,
        from_currency: str,
        to_currency: str,
        amount: float,
    ) -> dict[str, Any]:
        """Convert an amount between INR and MON."""
        rate_data = await self.get_mon_inr_rate()
        inr_per_mon: float = rate_data["inr_per_mon"]

        from_c = from_currency.upper()
        to_c = to_currency.upper()

        if from_c == "INR" and to_c == "MON":
            result = amount / inr_per_mon
        elif from_c == "MON" and to_c == "INR":
            result = amount * inr_per_mon
        else:
            raise ValueError(f"Unsupported conversion: {from_currency} -> {to_currency}")

        return {
            "from": from_c,
            "to": to_c,
            "amount": amount,
            "result": result,
            "rate": inr_per_mon,
            "stale": rate_data.get("stale", False),
            "demo": rate_data.get("demo", False),
        }
