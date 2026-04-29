from __future__ import annotations

from collections import deque
from statistics import median

from app.core.clock import utc_now_ms
from app.core.models import MetricsSnapshot, PortfolioSnapshot


class MetricsService:
    def __init__(self) -> None:
        self.decision_latency = deque(maxlen=4000)
        self.round_trip_latency = deque(maxlen=4000)
        self.event_timestamps = deque(maxlen=4000)
        self.fill_timestamps = deque(maxlen=4000)
        self.total_trades = 0

    def record_decision_latency(self, value_ms: float) -> None:
        self.decision_latency.append(value_ms)

    def record_round_trip_latency(self, value_ms: float) -> None:
        self.round_trip_latency.append(value_ms)

    def mark_event(self) -> None:
        self.event_timestamps.append(utc_now_ms())

    def mark_fill(self) -> None:
        self.fill_timestamps.append(utc_now_ms())
        self.total_trades += 1

    def snapshot(self, portfolio: PortfolioSnapshot) -> MetricsSnapshot:
        return MetricsSnapshot(
            decision_latency_ms=self._quantiles(self.decision_latency),
            round_trip_latency_ms=self._quantiles(self.round_trip_latency),
            events_per_sec=self._rate(self.event_timestamps),
            fills_per_sec=self._rate(self.fill_timestamps),
            total_trades=self.total_trades,
            inventories={position.symbol: position.net_qty for position in portfolio.positions},
        )

    def _rate(self, timestamps: deque[int]) -> float:
        cutoff = utc_now_ms() - 1000
        while timestamps and timestamps[0] < cutoff:
            timestamps.popleft()
        return float(len(timestamps))

    def _quantiles(self, values: deque[float]) -> dict[str, float]:
        if not values:
            return {"p50": 0.0, "p95": 0.0, "p99": 0.0}
        ordered = sorted(values)
        return {
            "p50": round(median(ordered), 3),
            "p95": round(ordered[min(len(ordered) - 1, int(len(ordered) * 0.95))], 3),
            "p99": round(ordered[min(len(ordered) - 1, int(len(ordered) * 0.99))], 3),
        }
