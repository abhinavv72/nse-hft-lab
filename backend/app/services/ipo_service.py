from __future__ import annotations

import asyncio
import time
from typing import Any

import httpx


class IpoService:
    """Cached client for NSE's public current-issue feed."""

    _URL = "https://www.nseindia.com/api/ipo-current-issue"

    def __init__(self, cache_seconds: int = 300) -> None:
        self.cache_seconds = cache_seconds
        self._cached: list[dict[str, Any]] = []
        self._cached_at = 0.0
        self._lock = asyncio.Lock()

    async def current_issues(self) -> dict[str, Any]:
        async with self._lock:
            if self._cached and time.monotonic() - self._cached_at < self.cache_seconds:
                return {"source": "NSE current issues", "cached": True, "issues": self._cached}

            headers = {
                "User-Agent": "Mozilla/5.0 (compatible; NSE-HFT-Lab/1.0)",
                "Accept": "application/json",
                "Accept-Language": "en-IN,en;q=0.9",
            }
            async with httpx.AsyncClient(headers=headers, timeout=12, follow_redirects=True) as client:
                response = await client.get(self._URL)
                response.raise_for_status()
                payload = response.json()
            if not isinstance(payload, list):
                raise ValueError("NSE current-issue response was not a list")
            self._cached = [self._normalise(item) for item in payload if isinstance(item, dict)]
            self._cached_at = time.monotonic()
            return {"source": "NSE current issues", "cached": False, "issues": self._cached}

    @staticmethod
    def _normalise(item: dict[str, Any]) -> dict[str, Any]:
        subscription = item.get("noOfTime")
        try:
            subscription = float(subscription) if subscription not in (None, "") else None
        except (TypeError, ValueError):
            subscription = None
        return {
            "company_name": item.get("companyName", "Unnamed issue"),
            "symbol": item.get("symbol", ""),
            "series": item.get("series", ""),
            "status": item.get("status", "Unknown"),
            "open_date": item.get("issueStartDate"),
            "close_date": item.get("issueEndDate"),
            "price_band": item.get("issuePrice") or "Not published by NSE feed",
            "issue_size_shares": item.get("issueSize"),
            "subscription_times": subscription,
            "shares_bid": item.get("noOfsharesBid"),
            "shares_offered": item.get("noOfSharesOffered"),
            "official_url": "https://www.nseindia.com/market-data/all-upcoming-issues-ipo",
        }
