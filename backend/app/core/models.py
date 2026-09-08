from __future__ import annotations

from collections import defaultdict
from typing import Any

from pydantic import BaseModel, Field

from app.core.enums import OrderStatus, OrderType, SessionMode, Side, StrategyKind


class DepthLevel(BaseModel):
    price: float
    qty: int


class BookSnapshot(BaseModel):
    symbol: str
    bids: list[DepthLevel] = Field(default_factory=list)
    asks: list[DepthLevel] = Field(default_factory=list)
    best_bid: float | None = None
    best_ask: float | None = None
    timestamp: str


class MarketTick(BaseModel):
    timestamp: str
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    vwap: float | None = None
    last_price: float
    mid_price: float
    spread: float
    volatility: float = 0.0


class OrderRequest(BaseModel):
    symbol: str
    side: Side
    order_type: OrderType = OrderType.LIMIT
    price: float = 0.0
    qty: int
    strategy_id: str | None = None
    owner: str = "manual"


class OrderRecord(BaseModel):
    order_id: str
    client_order_id: str | None = None
    symbol: str
    side: Side
    order_type: OrderType
    price: float
    qty: int
    remaining_qty: int
    filled_qty: int
    status: OrderStatus
    owner: str
    strategy_id: str | None = None
    timestamp: str
    latency_ms: float | None = None
    reject_reason: str | None = None


class TradeRecord(BaseModel):
    trade_id: str
    symbol: str
    price: float
    qty: int
    taker_order_id: str
    maker_order_id: str
    aggressor_side: Side
    timestamp: str
    source_owner: str | None = None


class StrategyConfig(BaseModel):
    strategy_id: str
    kind: StrategyKind
    symbol: str
    enabled: bool = False
    spread_bps: float = 8.0
    qty: int = 25
    aggression: float = 1.0
    threshold_bps: float = 12.0
    window: int = 8


class StrategyState(BaseModel):
    strategy_id: str
    kind: StrategyKind
    symbol: str
    enabled: bool
    config: StrategyConfig
    outstanding_orders: list[str] = Field(default_factory=list)
    last_action: str | None = None


class RiskState(BaseModel):
    kill_switch_enabled: bool = False
    max_order_qty: int
    max_position_per_symbol: int
    max_daily_loss: float
    max_price_deviation_bps: float
    stale_market_ms: int
    last_rejections: list[dict[str, Any]] = Field(default_factory=list)


class PositionSnapshot(BaseModel):
    symbol: str
    net_qty: int = 0
    avg_price: float = 0.0
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    mark_price: float = 0.0
    trade_count: int = 0
    fill_ratio: float = 0.0


class PortfolioSnapshot(BaseModel):
    positions: list[PositionSnapshot] = Field(default_factory=list)
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    total_pnl: float = 0.0
    total_trades: int = 0


class MetricsSnapshot(BaseModel):
    decision_latency_ms: dict[str, float] = Field(default_factory=dict)
    round_trip_latency_ms: dict[str, float] = Field(default_factory=dict)
    events_per_sec: float = 0.0
    fills_per_sec: float = 0.0
    total_trades: int = 0
    inventories: dict[str, int] = Field(default_factory=dict)


class LogEvent(BaseModel):
    timestamp: str
    level: str
    category: str
    message: str
    data: dict[str, Any] = Field(default_factory=dict)


class NewsArticle(BaseModel):
    article_id: str
    timestamp: str
    source: str
    headline: str
    summary: str = ""
    url: str = ""
    symbols: list[str] = Field(default_factory=list)
    sentiment: str = "neutral"
    impact_score: float = 0.0
    tags: list[str] = Field(default_factory=list)
    analysis_source: str = "rules"


class SignalIdea(BaseModel):
    signal_id: str
    symbol: str
    bias: str
    confidence: float
    score: float
    horizon: str = "today"
    last_price: float | None = None
    change_pct: float | None = None
    reasons: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    related_articles: list[str] = Field(default_factory=list)
    timestamp: str


class SessionState(BaseModel):
    session_id: str
    mode: SessionMode
    market_running: bool = False
    replay_running: bool = False
    speed: int = 1
    selected_symbol: str = "NIFTY"
    deterministic_seed: int = 42


class DashboardState(BaseModel):
    session: SessionState
    market: dict[str, MarketTick] = Field(default_factory=dict)
    order_books: dict[str, BookSnapshot] = Field(default_factory=dict)
    strategies: dict[str, StrategyState] = Field(default_factory=dict)
    orders: list[OrderRecord] = Field(default_factory=list)
    fills: list[TradeRecord] = Field(default_factory=list)
    risk: RiskState
    portfolio: PortfolioSnapshot
    metrics: MetricsSnapshot
    news: list[NewsArticle] = Field(default_factory=list)
    signals: list[SignalIdea] = Field(default_factory=list)
    logs: list[LogEvent] = Field(default_factory=list)


def empty_positions(symbols: list[str]) -> dict[str, PositionSnapshot]:
    return defaultdict(PositionSnapshot, {symbol: PositionSnapshot(symbol=symbol) for symbol in symbols})
