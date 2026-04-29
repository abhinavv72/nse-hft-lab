from __future__ import annotations

import asyncio
import json
import math
import subprocess
from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path

from app.core.clock import utc_now_iso
from app.core.enums import OrderStatus, OrderType, Side
from app.core.models import BookSnapshot, DepthLevel, OrderRecord, TradeRecord


@dataclass
class EngineResponse:
    order: OrderRecord | None
    trades: list[TradeRecord]
    snapshot: BookSnapshot


class _PythonOrder:
    def __init__(self, order_id: str, symbol: str, side: Side, order_type: OrderType, price: float, qty: int) -> None:
        self.order_id = order_id
        self.symbol = symbol
        self.side = side
        self.order_type = order_type
        self.price = price
        self.qty = qty
        self.remaining_qty = qty
        self.timestamp = utc_now_iso()


class _PythonBook:
    def __init__(self, symbol: str) -> None:
        self.symbol = symbol
        self.bids: dict[float, deque[str]] = defaultdict(deque)
        self.asks: dict[float, deque[str]] = defaultdict(deque)
        self.orders: dict[str, _PythonOrder] = {}

    def _sorted_prices(self, side: Side) -> list[float]:
        prices = self.bids.keys() if side == Side.BUY else self.asks.keys()
        return sorted(prices, reverse=side == Side.BUY)

    def snapshot(self, depth: int = 5) -> BookSnapshot:
        bids = [
            DepthLevel(
                price=price,
                qty=sum(self.orders[order_id].remaining_qty for order_id in self.bids[price] if order_id in self.orders),
            )
            for price in self._sorted_prices(Side.BUY)[:depth]
        ]
        asks = [
            DepthLevel(
                price=price,
                qty=sum(self.orders[order_id].remaining_qty for order_id in self.asks[price] if order_id in self.orders),
            )
            for price in self._sorted_prices(Side.SELL)[:depth]
        ]
        best_bid = bids[0].price if bids else None
        best_ask = asks[0].price if asks else None
        return BookSnapshot(symbol=self.symbol, bids=bids, asks=asks, best_bid=best_bid, best_ask=best_ask, timestamp=utc_now_iso())


class PythonEngineFallback:
    def __init__(self) -> None:
        self.books: dict[str, _PythonBook] = {}
        self.sequence = 0
        self.trade_sequence = 0

    def _book(self, symbol: str) -> _PythonBook:
        if symbol not in self.books:
            self.books[symbol] = _PythonBook(symbol)
        return self.books[symbol]

    def reset(self) -> None:
        self.books.clear()
        self.sequence = 0
        self.trade_sequence = 0

    def _next_order_id(self) -> str:
        self.sequence += 1
        return f"O{self.sequence:07d}"

    def _next_trade_id(self) -> str:
        self.trade_sequence += 1
        return f"T{self.trade_sequence:07d}"

    def submit(self, symbol: str, side: Side, order_type: OrderType, price: float, qty: int, owner: str, strategy_id: str | None) -> EngineResponse:
        if qty <= 0:
            raise ValueError("Invalid quantity")
        if order_type == OrderType.LIMIT and price <= 0:
            raise ValueError("Invalid price")
        book = self._book(symbol)
        order_id = self._next_order_id()
        incoming = _PythonOrder(order_id, symbol, side, order_type, price, qty)
        trades: list[TradeRecord] = []
        opposite_prices = book._sorted_prices(Side.SELL if side == Side.BUY else Side.BUY)

        def crossed(best_price: float) -> bool:
            if order_type == OrderType.MARKET:
                return True
            return best_price <= price if side == Side.BUY else best_price >= price

        for level_price in list(opposite_prices):
            if incoming.remaining_qty <= 0:
                break
            if not crossed(level_price):
                break
            queue = book.asks[level_price] if side == Side.BUY else book.bids[level_price]
            while queue and incoming.remaining_qty > 0:
                resting_id = queue[0]
                resting = book.orders.get(resting_id)
                if resting is None or resting.remaining_qty <= 0:
                    queue.popleft()
                    continue
                fill_qty = min(incoming.remaining_qty, resting.remaining_qty)
                incoming.remaining_qty -= fill_qty
                resting.remaining_qty -= fill_qty
                trades.append(
                    TradeRecord(
                        trade_id=self._next_trade_id(),
                        symbol=symbol,
                        price=resting.price,
                        qty=fill_qty,
                        taker_order_id=incoming.order_id,
                        maker_order_id=resting.order_id,
                        aggressor_side=side,
                        timestamp=utc_now_iso(),
                        source_owner=owner,
                    )
                )
                if resting.remaining_qty == 0:
                    queue.popleft()
                    del book.orders[resting.order_id]
            if not queue:
                if side == Side.BUY:
                    book.asks.pop(level_price, None)
                else:
                    book.bids.pop(level_price, None)

        status = OrderStatus.FILLED if incoming.remaining_qty == 0 else OrderStatus.PARTIAL if incoming.remaining_qty < incoming.qty else OrderStatus.ACCEPTED
        if incoming.remaining_qty > 0 and order_type == OrderType.LIMIT:
            book.orders[incoming.order_id] = incoming
            target = book.bids if side == Side.BUY else book.asks
            target[incoming.price].append(incoming.order_id)
        order = OrderRecord(
            order_id=incoming.order_id,
            symbol=symbol,
            side=side,
            order_type=order_type,
            price=price,
            qty=qty,
            remaining_qty=incoming.remaining_qty,
            filled_qty=qty - incoming.remaining_qty,
            status=status,
            owner=owner,
            strategy_id=strategy_id,
            timestamp=incoming.timestamp,
        )
        return EngineResponse(order=order, trades=trades, snapshot=book.snapshot())

    def cancel(self, symbol: str, order_id: str, owner: str = "manual") -> EngineResponse:
        book = self._book(symbol)
        order = book.orders.pop(order_id, None)
        if order is None:
            return EngineResponse(order=None, trades=[], snapshot=book.snapshot())
        levels = book.bids if order.side == Side.BUY else book.asks
        queue = levels.get(order.price)
        if queue:
            levels[order.price] = deque([item for item in queue if item != order_id])
            if not levels[order.price]:
                del levels[order.price]
        cancelled = OrderRecord(
            order_id=order.order_id,
            symbol=symbol,
            side=order.side,
            order_type=order.order_type,
            price=order.price,
            qty=order.qty,
            remaining_qty=0,
            filled_qty=order.qty - order.remaining_qty,
            status=OrderStatus.CANCELLED,
            owner=owner,
            timestamp=utc_now_iso(),
        )
        return EngineResponse(order=cancelled, trades=[], snapshot=book.snapshot())

    def snapshot(self, symbol: str, depth: int = 5) -> BookSnapshot:
        return self._book(symbol).snapshot(depth=depth)


class MatchingEngineAdapter:
    def __init__(self, executable_path: Path, fallback_executable_path: Path | None = None) -> None:
        self.executable_path = executable_path if executable_path.exists() else fallback_executable_path or executable_path
        self._use_subprocess = self.executable_path.exists()
        self._fallback = PythonEngineFallback()
        self._process: subprocess.Popen[str] | None = None
        self._loop_lock = asyncio.Lock()

    async def start(self) -> None:
        if not self._use_subprocess:
            return
        self._process = subprocess.Popen(
            [str(self.executable_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

    async def stop(self) -> None:
        if self._process and self._process.stdin:
            self._process.stdin.write("STOP\n")
            self._process.stdin.flush()
            self._process.terminate()
            self._process.wait(timeout=2)
        self._process = None

    async def reset(self) -> None:
        if self._use_subprocess:
            await self._send_command("RESET")
        self._fallback.reset()

    async def submit_order(
        self,
        symbol: str,
        side: Side,
        order_type: OrderType,
        price: float,
        qty: int,
        owner: str,
        strategy_id: str | None = None,
    ) -> EngineResponse:
        if not self._use_subprocess:
            return self._fallback.submit(symbol, side, order_type, price, qty, owner, strategy_id)
        command = f"SUBMIT\t{symbol}\t{side.value}\t{order_type.value}\t{price:.4f}\t{qty}\t{owner}\t{strategy_id or ''}"
        return await self._send_command(command)

    async def cancel_order(self, symbol: str, order_id: str, owner: str = "manual") -> EngineResponse:
        if not self._use_subprocess:
            return self._fallback.cancel(symbol, order_id, owner)
        return await self._send_command(f"CANCEL\t{symbol}\t{order_id}\t{owner}")

    async def get_snapshot(self, symbol: str, depth: int = 5) -> BookSnapshot:
        if not self._use_subprocess:
            return self._fallback.snapshot(symbol, depth)
        response = await self._send_command(f"SNAPSHOT\t{symbol}\t{depth}")
        return response.snapshot

    async def _send_command(self, command: str) -> EngineResponse:
        async with self._loop_lock:
            if self._process is None or self._process.stdin is None or self._process.stdout is None:
                raise RuntimeError("Matching engine process is not running")
            self._process.stdin.write(command + "\n")
            self._process.stdin.flush()
            order: OrderRecord | None = None
            trades: list[TradeRecord] = []
            snapshot: BookSnapshot | None = None
            while True:
                line = self._process.stdout.readline()
                if not line:
                    raise RuntimeError("Matching engine process terminated unexpectedly")
                text = line.strip()
                if text == "END":
                    break
                prefix, payload = text.split("\t", 1)
                data = json.loads(payload)
                if prefix == "ORDER":
                    order = OrderRecord.model_validate(data)
                elif prefix == "TRADE":
                    trades.append(TradeRecord.model_validate(data))
                elif prefix == "SNAPSHOT":
                    snapshot = BookSnapshot.model_validate(data)
            if snapshot is None:
                raise RuntimeError("Matching engine response missing snapshot")
            return EngineResponse(order=order, trades=trades, snapshot=snapshot)


def midpoint(snapshot: BookSnapshot) -> float:
    if snapshot.best_bid is None and snapshot.best_ask is None:
        return 0.0
    if snapshot.best_bid is None:
        return snapshot.best_ask or 0.0
    if snapshot.best_ask is None:
        return snapshot.best_bid
    return (snapshot.best_bid + snapshot.best_ask) / 2.0


def safe_bps(base_price: float, other_price: float) -> float:
    if not base_price or math.isclose(base_price, 0.0):
        return 0.0
    return ((other_price - base_price) / base_price) * 10000.0
