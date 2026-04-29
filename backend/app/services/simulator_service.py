from __future__ import annotations

import asyncio
import uuid
from collections import deque

from app.core.clock import utc_now_iso
from app.core.enums import SessionMode
from app.core.models import DashboardState, LogEvent, SessionState
from app.services.market_data_service import MarketDataService
from app.services.metrics_service import MetricsService
from app.services.news_ingestion_service import NewsIngestionService
from app.services.order_gateway import OrderGateway
from app.services.persistence_service import PersistenceService
from app.services.portfolio_service import PortfolioService
from app.services.replay_service import ReplayService
from app.services.risk_service import RiskService
from app.services.signal_service import SignalService
from app.services.strategy_service import StrategyService


class SimulatorService:
    def __init__(
        self,
        market_data: MarketDataService,
        gateway: OrderGateway,
        strategy: StrategyService,
        risk: RiskService,
        portfolio: PortfolioService,
        metrics: MetricsService,
        persistence: PersistenceService,
        replay: ReplayService,
        news: NewsIngestionService,
        signals: SignalService,
        seed: int,
    ) -> None:
        self.market_data = market_data
        self.gateway = gateway
        self.strategy = strategy
        self.risk = risk
        self.portfolio = portfolio
        self.metrics = metrics
        self.persistence = persistence
        self.replay = replay
        self.news = news
        self.signals = signals
        self.seed = seed
        self.latest_ticks: dict[str, dict] = {}
        self.logs: deque[LogEvent] = deque(maxlen=200)
        self.session = SessionState(
            session_id=self._new_session_id(),
            mode=SessionMode.LIVE,
            market_running=False,
            replay_running=False,
            speed=1,
            selected_symbol="NIFTY",
            deterministic_seed=seed,
        )
        self._task: asyncio.Task | None = None
        self._replay_rows: dict[str, list[dict]] | None = None
        self._volatility_multiplier = 1.0

    def _new_session_id(self) -> str:
        return f"session-{uuid.uuid4().hex[:8]}"

    async def start_market(self, speed: int = 1, mode: str = "live", replay_session_id: str | None = None) -> SessionState:
        self.session.speed = speed
        self.session.mode = SessionMode.REPLAY if mode == "replay" else SessionMode.LIVE
        self.session.market_running = True
        self.session.replay_running = mode == "replay"
        self._replay_rows = self.replay.load_ticks(replay_session_id) if replay_session_id else None
        self._log("INFO", "market", "market started", {"mode": mode, "speed": speed, "replay_session_id": replay_session_id})
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._run_loop())
        return self.session

    async def stop_market(self) -> SessionState:
        self.session.market_running = False
        self.session.replay_running = False
        self._log("INFO", "market", "market stopped", {})
        return self.session

    async def reset_session(self) -> SessionState:
        self.session = SessionState(
            session_id=self._new_session_id(),
            mode=SessionMode.LIVE,
            market_running=False,
            replay_running=False,
            speed=1,
            selected_symbol=self.session.selected_symbol,
            deterministic_seed=self.seed,
        )
        self.market_data.reset()
        self.portfolio.reset()
        self.risk.reset()
        self.gateway.reset()
        await self.gateway.engine.reset()
        self.latest_ticks.clear()
        self.logs.clear()
        self._volatility_multiplier = 1.0
        for article in self.news.latest():
            await self.persistence.persist_news(self.session.session_id, article)
        await self.refresh_signals()
        self._log("INFO", "market", "session reset", {"session_id": self.session.session_id})
        return self.session

    async def inject_volatility_spike(self) -> dict[str, float]:
        self._volatility_multiplier = 3.0
        self._log("WARN", "market", "volatility spike injected", {"multiplier": self._volatility_multiplier})
        return {"volatility_multiplier": self._volatility_multiplier}

    async def select_symbol(self, symbol: str) -> SessionState:
        self.session.selected_symbol = symbol
        return self.session

    def _log(self, level: str, category: str, message: str, data: dict) -> None:
        self.logs.appendleft(LogEvent(timestamp=utc_now_iso(), level=level, category=category, message=message, data=data))

    async def refresh_news(self) -> list:
        added = await self.news.refresh()
        for article in added:
            await self.persistence.persist_news(self.session.session_id, article)
        await self.refresh_signals()
        if added:
            self._log("INFO", "news", "news feed refreshed", {"articles_added": len(added)})
        return added

    async def refresh_signals(self) -> None:
        signals = self.signals.recompute(self.latest_ticks, self.news.latest())
        await self.persistence.replace_signals(self.session.session_id, signals)

    async def _run_loop(self) -> None:
        while True:
            if not self.session.market_running:
                await asyncio.sleep(0.2)
                continue

            for symbol in self.market_data.symbols:
                rows = self._replay_rows.get(symbol) if self._replay_rows else None
                tick = self.market_data.next_tick(symbol, source_rows=rows)
                self.latest_ticks[symbol] = tick.model_dump()
                self.metrics.mark_event()
                self.risk.update_market_timestamp(symbol)
                self.portfolio.mark_market(symbol, tick.last_price)
                depth = self.market_data.synthetic_depth(tick, volatility_multiplier=self._volatility_multiplier)
                book = await self.gateway.sync_market_depth(self.session.session_id, symbol, depth.bids, depth.asks)
                await self.strategy.on_market_tick(self.session.session_id, tick, book)
                await self.persistence.persist_tick(self.session.session_id, tick.model_dump())

            if self._volatility_multiplier > 1.0:
                self._volatility_multiplier = max(1.0, round(self._volatility_multiplier - 0.35, 2))
            await self.refresh_signals()
            await self.persistence.persist_portfolio(self.session.session_id, self.portfolio.snapshot())
            await asyncio.sleep(max(0.08, 0.75 / max(self.session.speed, 1)))

    def dashboard_state(self) -> DashboardState:
        portfolio = self.portfolio.snapshot()
        return DashboardState(
            session=self.session,
            market=self.latest_ticks,
            order_books=self.gateway.latest_books,
            strategies=self.strategy.snapshot(),
            orders=self.gateway.ui_orders(),
            fills=self.gateway.ui_fills(),
            risk=self.risk.snapshot(),
            portfolio=portfolio,
            metrics=self.metrics.snapshot(portfolio),
            news=self.news.latest(),
            signals=self.signals.latest(),
            logs=list(self.logs),
        )
