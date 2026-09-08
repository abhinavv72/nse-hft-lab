from __future__ import annotations

import asyncio
import importlib
import logging
from collections.abc import Mapping

logger = logging.getLogger(__name__)


class LivePriceService:
    """Fetches latest prices from yfinance with a background refresh cadence."""

    def __init__(self, symbol_map: Mapping[str, str], enabled: bool = True) -> None:
        self.symbol_map = dict(symbol_map)
        self.enabled = enabled
        self._latest: dict[str, dict] = {}
        self._lock = asyncio.Lock()
        self._yf = None

    def _client(self):
        if self._yf is not None:
            return self._yf
        try:
            self._yf = importlib.import_module("yfinance")
        except Exception:
            self._yf = False
        return self._yf

    async def refresh(self) -> dict[str, dict]:
        """Refresh all symbols concurrently; always returns the last known good prices."""
        if not self.enabled:
            return self._latest
        yf = self._client()
        if not yf:
            return self._latest

        tasks = {
            symbol: asyncio.to_thread(self._fetch_one, yf, ticker)
            for symbol, ticker in self.symbol_map.items()
        }
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)

        async with self._lock:
            for symbol, result in zip(tasks.keys(), results):
                if isinstance(result, dict) and result:
                    self._latest[symbol] = result
                elif isinstance(result, Exception):
                    logger.debug("yfinance fetch failed for %s: %s", symbol, result)

        return dict(self._latest)

    def latest(self) -> dict[str, dict]:
        return dict(self._latest)

    def get(self, symbol: str) -> dict | None:
        return self._latest.get(symbol)

    @staticmethod
    def _fetch_one(yf, ticker_symbol: str) -> dict | None:
        try:
            ticker = yf.Ticker(ticker_symbol)
            info = ticker.fast_info

            # yfinance >=0.2 uses attribute access, not dict .get()
            last_price = getattr(info, "last_price", None) or getattr(info, "regularMarketPrice", None)
            if not last_price or last_price <= 0:
                return None

            open_price   = getattr(info, "open", None) or last_price
            day_high     = getattr(info, "day_high", None) or last_price
            day_low      = getattr(info, "day_low", None) or last_price
            volume       = int(getattr(info, "last_volume", None) or 0)
            prev_close   = getattr(info, "previous_close", None) or last_price

            return {
                "last_price": float(last_price),
                "open":       float(open_price) if open_price > 0 else float(last_price),
                "high":       float(day_high)   if day_high > 0   else float(last_price),
                "low":        float(day_low)    if day_low > 0    else float(last_price),
                "prev_close": float(prev_close),
                "volume":     volume,
                "volatility": float((day_high - day_low) / last_price) if last_price > 0 else 0.0,
                "source":     "yfinance",
            }
        except Exception as exc:
            logger.debug("LivePriceService._fetch_one(%s) error: %s", ticker_symbol, exc)
            return None
