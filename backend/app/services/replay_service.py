from __future__ import annotations

from collections import defaultdict


class ReplayService:
    def __init__(self, persistence_service) -> None:
        self.persistence = persistence_service

    def list_sessions(self) -> list[str]:
        return self.persistence.list_sessions()

    def load_ticks(self, session_id: str) -> dict[str, list[dict]]:
        rows = self.persistence.fetch_ticks(session_id)
        grouped: dict[str, list[dict]] = defaultdict(list)
        for row in rows:
            price = float(row["last_price"])
            grouped[row["symbol"]].append(
                {
                    "timestamp": row["timestamp"],
                    "symbol": row["symbol"],
                    "open": price,
                    "high": round(price * (1 + row["volatility"]), 2),
                    "low": round(price * max(0.9, 1 - row["volatility"]), 2),
                    "close": price,
                    "volume": int(row["volume"]),
                    "vwap": float(row["mid_price"]),
                }
            )
        return grouped
