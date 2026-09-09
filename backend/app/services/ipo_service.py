from __future__ import annotations

import asyncio
import re
import time
from typing import Any

import httpx


class IpoService:
    """Cached client for NSE's public current-issue feed."""

    _URL = "https://www.nseindia.com/api/ipo-current-issue"
    _GURU_URL = "https://www.ipoguru.in/api/v1/ipos"

    def __init__(self, api_key: str = "", cache_seconds: int = 300) -> None:
        self.api_key = api_key.strip()
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
                guru_issues = await self._fetch_guru_issues(client)
            if not isinstance(payload, list):
                raise ValueError("NSE current-issue response was not a list")
            self._cached = [self._normalise(item, self._find_guru_match(item, guru_issues)) for item in payload if isinstance(item, dict)]
            self._cached_at = time.monotonic()
            return {"source": "NSE current issues", "cached": False, "issues": self._cached}

    async def _fetch_guru_issues(self, client: httpx.AsyncClient) -> list[dict[str, Any]]:
        """Fetch optional GMP/lot-size enrichment without making the NSE feed depend on it."""
        if not self.api_key:
            return []
        try:
            response = await client.get(self._GURU_URL, headers={"X-API-KEY": self.api_key})
            response.raise_for_status()
            data = response.json().get("data", [])
            return data if isinstance(data, list) else []
        except (httpx.HTTPError, ValueError, AttributeError):
            return []

    @staticmethod
    def _name_key(value: str) -> str:
        return re.sub(r"[^a-z0-9]", "", re.sub(r"\b(limited|ltd|india)\b", "", value.lower()))

    def _find_guru_match(self, nse_issue: dict[str, Any], guru_issues: list[dict[str, Any]]) -> dict[str, Any] | None:
        target = self._name_key(str(nse_issue.get("companyName", "")))
        for issue in guru_issues:
            candidate = self._name_key(str(issue.get("name", "")))
            if target and candidate and (target == candidate or target in candidate or candidate in target):
                return issue
        return None

    @staticmethod
    def _normalise(item: dict[str, Any], guru: dict[str, Any] | None = None) -> dict[str, Any]:
        subscription = item.get("noOfTime")
        try:
            subscription = float(subscription) if subscription not in (None, "") else None
        except (TypeError, ValueError):
            subscription = None
        gmp = guru.get("gmp") if guru else None
        subscription_data = guru.get("subscription") if guru else None
        lot_size = guru.get("lot_size") if guru else None
        price_band = item.get("issuePrice") or (guru.get("price_band") if guru else None) or "Not published by NSE feed"
        try:
            lot_size = int(str(lot_size)) if lot_size not in (None, "") else None
        except (TypeError, ValueError):
            lot_size = None
        try:
            gmp_value = float(gmp.get("price")) if isinstance(gmp, dict) and gmp.get("price") not in (None, "") else None
        except (TypeError, ValueError):
            gmp_value = None
        return {
            "company_name": item.get("companyName", "Unnamed issue"),
            "symbol": item.get("symbol", ""),
            "series": item.get("series", ""),
            "status": item.get("status", "Unknown"),
            "open_date": item.get("issueStartDate"),
            "close_date": item.get("issueEndDate"),
            "price_band": price_band,
            "issue_size_shares": item.get("issueSize"),
            "subscription_times": subscription,
            "shares_bid": item.get("noOfsharesBid"),
            "shares_offered": item.get("noOfSharesOffered"),
            "official_url": "https://www.nseindia.com/market-data/all-upcoming-issues-ipo",
            "lot_size": lot_size,
            "gmp": gmp_value,
            "gmp_updated_at": gmp.get("updated_at") if isinstance(gmp, dict) else None,
            "gmp_source": "IPO Guru" if gmp_value is not None else None,
            "retail_subscription": subscription_data.get("retail") if isinstance(subscription_data, dict) else None,
            "registrar": guru.get("registrar") if guru else None,
        }
