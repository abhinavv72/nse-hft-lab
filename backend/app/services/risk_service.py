from __future__ import annotations

from collections import deque

from app.config import AppConfig
from app.core.clock import utc_now_iso, utc_now_ms
from app.core.enums import OrderType, Side
from app.core.models import OrderRequest, PortfolioSnapshot, RiskState


class RiskService:
    def __init__(self, config: AppConfig) -> None:
        self._state = RiskState(
            kill_switch_enabled=config.kill_switch_enabled,
            max_order_qty=config.max_order_qty,
            max_position_per_symbol=config.max_position_per_symbol,
            max_daily_loss=config.max_daily_loss,
            max_price_deviation_bps=config.max_price_deviation_bps,
            stale_market_ms=config.stale_market_ms,
        )
        self._rejections = deque(maxlen=50)
        self._last_market_ms: dict[str, int] = {}

    def reset(self) -> None:
        self._rejections.clear()
        self._last_market_ms.clear()

    def update_market_timestamp(self, symbol: str) -> None:
        self._last_market_ms[symbol] = utc_now_ms()

    def set_kill_switch(self, enabled: bool) -> None:
        self._state.kill_switch_enabled = enabled

    def update_limits(self, payload: dict) -> RiskState:
        for key in ("max_order_qty", "max_position_per_symbol", "max_daily_loss", "max_price_deviation_bps", "stale_market_ms"):
            if key in payload and payload[key] is not None:
                setattr(self._state, key, payload[key])
        return self.snapshot()

    def check_order(self, request: OrderRequest, market_price: float | None, portfolio: PortfolioSnapshot) -> tuple[bool, str | None]:
        if self._state.kill_switch_enabled:
            return self._reject("Kill switch active", request)
        if request.qty <= 0 or request.qty > self._state.max_order_qty:
            return self._reject("Order quantity exceeds limit", request)
        last_market_ms = self._last_market_ms.get(request.symbol)
        if last_market_ms is None or utc_now_ms() - last_market_ms > self._state.stale_market_ms:
            return self._reject("Stale market data", request)
        if request.order_type == OrderType.LIMIT and market_price and market_price > 0:
            deviation_bps = abs((request.price - market_price) / market_price) * 10000.0
            if deviation_bps > self._state.max_price_deviation_bps:
                return self._reject("Price band exceeded", request)
        if portfolio.total_pnl <= -abs(self._state.max_daily_loss):
            return self._reject("Daily loss limit breached", request)
        current_position = next((item.net_qty for item in portfolio.positions if item.symbol == request.symbol), 0)
        projected = current_position + (request.qty if request.side == Side.BUY else -request.qty)
        if abs(projected) > self._state.max_position_per_symbol:
            return self._reject("Position limit exceeded", request)
        return True, None

    def _reject(self, reason: str, request: OrderRequest) -> tuple[bool, str]:
        self._rejections.appendleft(
            {"timestamp": utc_now_iso(), "symbol": request.symbol, "owner": request.owner, "reason": reason, "qty": request.qty}
        )
        return False, reason

    def snapshot(self) -> RiskState:
        state = self._state.model_copy(deep=True)
        state.last_rejections = list(self._rejections)
        return state
