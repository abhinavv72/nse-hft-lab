from __future__ import annotations

import csv
import random
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from app.core.models import DepthLevel, MarketTick


@dataclass
class SyntheticDepth:
    bids: list[DepthLevel]
    asks: list[DepthLevel]


class MarketDataService:
    def __init__(self, data_dir: Path, symbols: list[str], seed: int) -> None:
        self.data_dir = data_dir
        self.symbols = symbols
        self.random = random.Random(seed)
        self.rows_by_symbol: dict[str, list[dict[str, str]]] = defaultdict(list)
        self.indices: dict[str, int] = {}
        self._load()

    def _load(self) -> None:
        for csv_path in sorted(self.data_dir.glob("*_sample.csv")):
            with csv_path.open("r", encoding="utf-8") as handle:
                reader = csv.DictReader(handle)
                if not reader.fieldnames or "symbol" not in reader.fieldnames:
                    continue
                for row in reader:
                    self.rows_by_symbol[row["symbol"]].append(row)
        for symbol in self.symbols:
            self.indices[symbol] = 0

    def reset(self) -> None:
        for symbol in self.symbols:
            self.indices[symbol] = 0

    def next_tick(self, symbol: str, source_rows: list[dict[str, str]] | None = None) -> MarketTick:
        rows = source_rows or self.rows_by_symbol[symbol]
        if not rows:
            raise ValueError(f"No market data found for {symbol}")
        index = self.indices[symbol] % len(rows)
        self.indices[symbol] += 1
        row = rows[index]
        close_price = float(row["close"])
        high_price = float(row["high"])
        low_price = float(row["low"])
        spread = max(close_price * 0.0004, 0.05)
        return MarketTick(
            timestamp=row["timestamp"],
            symbol=row["symbol"],
            open=float(row["open"]),
            high=high_price,
            low=low_price,
            close=close_price,
            volume=int(float(row["volume"])),
            vwap=float(row.get("vwap") or close_price),
            last_price=close_price,
            mid_price=close_price,
            spread=spread,
            volatility=(high_price - low_price) / max(close_price, 1.0),
        )

    def synthetic_depth(self, tick: MarketTick, depth: int = 5, volatility_multiplier: float = 1.0) -> SyntheticDepth:
        half_spread = max(tick.spread * volatility_multiplier / 2.0, 0.05)
        price_gap = max(tick.last_price * 0.0002, 0.05)
        bids: list[DepthLevel] = []
        asks: list[DepthLevel] = []
        for level in range(depth):
            base_qty = max(10, int(tick.volume / 8000))
            bid_price = round(max(tick.mid_price - half_spread - level * price_gap, 0.05), 2)
            ask_price = round(max(tick.mid_price + half_spread + level * price_gap, bid_price + 0.05), 2)
            qty = base_qty + (depth - level) * 4 + self.random.randint(0, 6)
            bids.append(DepthLevel(price=bid_price, qty=qty))
            asks.append(DepthLevel(price=ask_price, qty=qty + self.random.randint(0, 4)))
        return SyntheticDepth(bids=bids, asks=asks)
