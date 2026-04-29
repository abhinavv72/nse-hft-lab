from __future__ import annotations

from dataclasses import dataclass

from app.adapters.duckdb_adapter import LocalAnalyticsStore
from app.adapters.matching_engine_adapter import MatchingEngineAdapter
from app.core.event_bus import EventBus
from app.services.market_data_service import MarketDataService
from app.services.metrics_service import MetricsService
from app.services.news_ingestion_service import NewsIngestionService
from app.services.order_gateway import OrderGateway
from app.services.persistence_service import PersistenceService
from app.services.portfolio_service import PortfolioService
from app.services.replay_service import ReplayService
from app.services.risk_service import RiskService
from app.services.signal_service import SignalService
from app.services.simulator_service import SimulatorService
from app.services.strategy_service import StrategyService


@dataclass
class ServiceContainer:
    event_bus: EventBus
    store: LocalAnalyticsStore
    market_data: MarketDataService
    engine: MatchingEngineAdapter
    persistence: PersistenceService
    metrics: MetricsService
    news: NewsIngestionService
    signals: SignalService
    portfolio: PortfolioService
    risk: RiskService
    gateway: OrderGateway
    strategy: StrategyService
    replay: ReplayService
    simulator: SimulatorService
