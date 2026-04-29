from __future__ import annotations

from collections import deque

from app.adapters.matching_engine_adapter import MatchingEngineAdapter
from app.core.clock import utc_now_iso, utc_now_ms
from app.core.enums import OrderStatus, Side
from app.core.models import BookSnapshot, OrderRecord, OrderRequest, TradeRecord
from app.services.metrics_service import MetricsService
from app.services.persistence_service import PersistenceService
from app.services.portfolio_service import PortfolioService
from app.services.risk_service import RiskService


class OrderGateway:
    def __init__(
        self,
        engine: MatchingEngineAdapter,
        risk: RiskService,
        portfolio: PortfolioService,
        metrics: MetricsService,
        persistence: PersistenceService,
    ) -> None:
        self.engine = engine
        self.risk = risk
        self.portfolio = portfolio
        self.metrics = metrics
        self.persistence = persistence
        self.latest_books: dict[str, BookSnapshot] = {}
        self.order_owners: dict[str, str] = {}
        self.order_sides: dict[str, Side] = {}
        self.recent_orders: deque[OrderRecord] = deque(maxlen=200)
        self.recent_fills: deque[TradeRecord] = deque(maxlen=200)
        self.synthetic_order_ids: dict[str, list[str]] = {}

    def reset(self) -> None:
        self.latest_books.clear()
        self.order_owners.clear()
        self.order_sides.clear()
        self.recent_orders.clear()
        self.recent_fills.clear()
        self.synthetic_order_ids.clear()

    async def submit_order(self, session_id: str, request: OrderRequest, market_price: float | None, bypass_risk: bool = False) -> OrderRecord:
        start_ms = utc_now_ms()
        if not bypass_risk:
            approved, reason = self.risk.check_order(request, market_price, self.portfolio.snapshot())
            if not approved:
                rejected = OrderRecord(
                    order_id=f"RJ-{utc_now_ms()}",
                    symbol=request.symbol,
                    side=request.side,
                    order_type=request.order_type,
                    price=request.price,
                    qty=request.qty,
                    remaining_qty=request.qty,
                    filled_qty=0,
                    status=OrderStatus.REJECTED,
                    owner=request.owner,
                    strategy_id=request.strategy_id,
                    timestamp=utc_now_iso(),
                    reject_reason=reason,
                )
                self.recent_orders.appendleft(rejected)
                await self.persistence.persist_order(session_id, rejected)
                return rejected

        response = await self.engine.submit_order(
            symbol=request.symbol,
            side=request.side,
            order_type=request.order_type,
            price=request.price,
            qty=request.qty,
            owner=request.owner,
            strategy_id=request.strategy_id,
        )
        if response.order is None:
            raise RuntimeError("Matching engine returned no ack")
        response.order.latency_ms = round(utc_now_ms() - start_ms, 3)
        self.metrics.record_round_trip_latency(response.order.latency_ms)
        self.order_owners[response.order.order_id] = request.owner
        self.order_sides[response.order.order_id] = request.side
        self.latest_books[request.symbol] = response.snapshot

        if request.owner != "market_sim":
            self.portfolio.register_order(request.symbol)
            self.recent_orders.appendleft(response.order)
            await self.persistence.persist_order(session_id, response.order)

        for trade in response.trades:
            await self._handle_trade(session_id, trade)
        return response.order

    async def cancel_order(self, session_id: str, symbol: str, order_id: str, owner: str = "manual") -> OrderRecord | None:
        response = await self.engine.cancel_order(symbol=symbol, order_id=order_id, owner=owner)
        self.latest_books[symbol] = response.snapshot
        if response.order and owner != "market_sim":
            self.recent_orders.appendleft(response.order)
            await self.persistence.persist_order(session_id, response.order)
        return response.order

    async def sync_market_depth(self, session_id: str, symbol: str, bids: list, asks: list) -> BookSnapshot:
        for order_id in self.synthetic_order_ids.get(symbol, []):
            await self.cancel_order(session_id, symbol, order_id, owner="market_sim")
        self.synthetic_order_ids[symbol] = []

        for level in bids:
            order = await self.submit_order(
                session_id,
                OrderRequest(symbol=symbol, side=Side.BUY, price=level.price, qty=level.qty, owner="market_sim"),
                market_price=level.price,
                bypass_risk=True,
            )
            self.synthetic_order_ids[symbol].append(order.order_id)
        for level in asks:
            order = await self.submit_order(
                session_id,
                OrderRequest(symbol=symbol, side=Side.SELL, price=level.price, qty=level.qty, owner="market_sim"),
                market_price=level.price,
                bypass_risk=True,
            )
            self.synthetic_order_ids[symbol].append(order.order_id)

        snapshot = await self.engine.get_snapshot(symbol)
        self.latest_books[symbol] = snapshot
        return snapshot

    async def _handle_trade(self, session_id: str, trade: TradeRecord) -> None:
        taker_owner = self.order_owners.get(trade.taker_order_id)
        maker_owner = self.order_owners.get(trade.maker_order_id)
        taker_side = self.order_sides.get(trade.taker_order_id, trade.aggressor_side)
        maker_side = Side.SELL if taker_side == Side.BUY else Side.BUY

        if taker_owner and taker_owner != "market_sim":
            self.portfolio.apply_fill(trade.symbol, taker_side, trade.qty, trade.price)
        if maker_owner and maker_owner != "market_sim":
            self.portfolio.apply_fill(trade.symbol, maker_side, trade.qty, trade.price)

        self.metrics.mark_fill()
        self.recent_fills.appendleft(trade)
        if taker_owner != "market_sim" or maker_owner != "market_sim":
            await self.persistence.persist_fill(session_id, trade)

    def ui_orders(self) -> list[OrderRecord]:
        return list(self.recent_orders)

    def ui_fills(self) -> list[TradeRecord]:
        return list(self.recent_fills)
