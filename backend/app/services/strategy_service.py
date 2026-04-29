from __future__ import annotations

from collections import defaultdict, deque

from app.core.clock import utc_now_iso, utc_now_ms
from app.core.enums import OrderStatus, OrderType, Side, StrategyKind
from app.core.models import MarketTick, OrderRequest, StrategyConfig, StrategyState
from app.services.metrics_service import MetricsService
from app.services.order_gateway import OrderGateway
from app.services.portfolio_service import PortfolioService


class StrategyService:
    def __init__(self, gateway: OrderGateway, portfolio: PortfolioService, metrics: MetricsService, max_position_per_symbol: int) -> None:
        self.gateway = gateway
        self.portfolio = portfolio
        self.metrics = metrics
        self.max_position_per_symbol = max_position_per_symbol
        self.price_windows: dict[str, deque[float]] = defaultdict(lambda: deque(maxlen=32))
        self.last_signal_ms: dict[str, int] = {}
        self.strategies: dict[str, StrategyState] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        defaults = [
            StrategyConfig(strategy_id="mm-nifty", kind=StrategyKind.MARKET_MAKER, symbol="NIFTY"),
            StrategyConfig(strategy_id="mr-reliance", kind=StrategyKind.MEAN_REVERSION, symbol="RELIANCE"),
        ]
        for config in defaults:
            self.strategies[config.strategy_id] = StrategyState(
                strategy_id=config.strategy_id,
                kind=config.kind,
                symbol=config.symbol,
                enabled=False,
                config=config,
            )

    async def start(self, strategy_id: str, payload: dict) -> StrategyState:
        state = self.strategies[strategy_id]
        state.config = state.config.model_copy(update=payload)
        state.symbol = state.config.symbol
        state.enabled = True
        state.last_action = f"started@{utc_now_iso()}"
        return state

    async def stop(self, session_id: str, strategy_id: str) -> StrategyState:
        state = self.strategies[strategy_id]
        for order_id in list(state.outstanding_orders):
            await self.gateway.cancel_order(session_id, state.symbol, order_id, owner=f"strategy:{strategy_id}")
        state.outstanding_orders.clear()
        state.enabled = False
        state.last_action = f"stopped@{utc_now_iso()}"
        return state

    async def update(self, strategy_id: str, payload: dict) -> StrategyState:
        state = self.strategies[strategy_id]
        state.config = state.config.model_copy(update=payload)
        state.symbol = state.config.symbol
        return state

    async def on_market_tick(self, session_id: str, tick: MarketTick, book_snapshot) -> None:
        self.price_windows[tick.symbol].append(tick.last_price)
        for state in self.strategies.values():
            if not state.enabled or state.symbol != tick.symbol:
                continue
            started_ms = utc_now_ms()
            if state.kind == StrategyKind.MARKET_MAKER:
                await self._market_make(session_id, state, tick, book_snapshot)
            else:
                await self._mean_revert(session_id, state, tick)
            self.metrics.record_decision_latency(utc_now_ms() - started_ms)

    async def _market_make(self, session_id: str, state: StrategyState, tick: MarketTick, book_snapshot) -> None:
        position = self.portfolio.positions[state.symbol].net_qty
        inventory_skew = (position / max(self.max_position_per_symbol, 1)) * tick.last_price * 0.0002
        mid = tick.mid_price
        if book_snapshot and book_snapshot.best_bid and book_snapshot.best_ask:
            mid = (book_snapshot.best_bid + book_snapshot.best_ask) / 2.0
        spread_bps = state.config.spread_bps * max(1.0, tick.volatility * 100)
        half_spread = max(mid * (spread_bps / 10000.0) / 2.0, 0.05)
        bid_price = round(max(mid - half_spread - inventory_skew, 0.05), 2)
        ask_price = round(max(mid + half_spread - inventory_skew, bid_price + 0.05), 2)

        for order_id in list(state.outstanding_orders):
            await self.gateway.cancel_order(session_id, state.symbol, order_id, owner=f"strategy:{state.strategy_id}")
        state.outstanding_orders.clear()

        buy = await self.gateway.submit_order(
            session_id,
            OrderRequest(
                symbol=state.symbol,
                side=Side.BUY,
                price=bid_price,
                qty=int(state.config.qty),
                owner=f"strategy:{state.strategy_id}",
                strategy_id=state.strategy_id,
            ),
            market_price=tick.last_price,
        )
        sell = await self.gateway.submit_order(
            session_id,
            OrderRequest(
                symbol=state.symbol,
                side=Side.SELL,
                price=ask_price,
                qty=int(state.config.qty),
                owner=f"strategy:{state.strategy_id}",
                strategy_id=state.strategy_id,
            ),
            market_price=tick.last_price,
        )
        if buy.status != OrderStatus.REJECTED:
            state.outstanding_orders.append(buy.order_id)
        if sell.status != OrderStatus.REJECTED:
            state.outstanding_orders.append(sell.order_id)
        state.last_action = f"quoted {bid_price}/{ask_price}"

    async def _mean_revert(self, session_id: str, state: StrategyState, tick: MarketTick) -> None:
        now_ms = utc_now_ms()
        if now_ms - self.last_signal_ms.get(state.strategy_id, 0) < 750:
            return
        window = self.price_windows[state.symbol]
        if len(window) < max(3, state.config.window):
            return
        recent = list(window)[-state.config.window :]
        mean_price = sum(recent) / len(recent)
        deviation_bps = ((tick.last_price - mean_price) / mean_price) * 10000.0
        if abs(deviation_bps) < state.config.threshold_bps:
            return
        side = Side.SELL if deviation_bps > 0 else Side.BUY
        await self.gateway.submit_order(
            session_id,
            OrderRequest(
                symbol=state.symbol,
                side=side,
                order_type=OrderType.MARKET,
                price=tick.last_price,
                qty=int(max(1, state.config.qty * state.config.aggression)),
                owner=f"strategy:{state.strategy_id}",
                strategy_id=state.strategy_id,
            ),
            market_price=tick.last_price,
        )
        self.last_signal_ms[state.strategy_id] = now_ms
        state.last_action = f"signal {side.value}"

    def snapshot(self) -> dict[str, StrategyState]:
        return self.strategies
