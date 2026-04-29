from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.adapters.duckdb_adapter import LocalAnalyticsStore
from app.adapters.matching_engine_adapter import MatchingEngineAdapter
from app.api.routes_market import router as market_router
from app.api.routes_metrics import router as metrics_router
from app.api.routes_news import router as news_router
from app.api.routes_portfolio import router as portfolio_router
from app.api.routes_replay import router as replay_router
from app.api.routes_risk import router as risk_router
from app.api.routes_signals import router as signals_router
from app.api.routes_strategy import router as strategy_router
from app.config import get_config
from app.core.container import ServiceContainer
from app.core.event_bus import EventBus
from app.services.event_classifier_service import EventClassifierService
from app.services.market_data_service import MarketDataService
from app.services.metrics_service import MetricsService
from app.services.news_ingestion_service import NewsIngestionService
from app.services.order_gateway import OrderGateway
from app.services.persistence_service import PersistenceService
from app.services.portfolio_service import PortfolioService
from app.services.replay_service import ReplayService
from app.services.risk_service import RiskService
from app.services.sentiment_service import SentimentService
from app.services.signal_service import SignalService
from app.services.simulator_service import SimulatorService
from app.services.symbol_mapper_service import SymbolMapperService
from app.services.strategy_service import StrategyService
from app.websocket_manager import WebSocketManager


config = get_config()
ws_manager = WebSocketManager()
services: ServiceContainer | None = None
broadcast_task: asyncio.Task | None = None
news_refresh_task: asyncio.Task | None = None


def build_services() -> ServiceContainer:
    event_bus = EventBus()
    store = LocalAnalyticsStore(config.db_path)
    market_data = MarketDataService(config.data_dir, config.market_symbols, config.deterministic_seed)
    engine = MatchingEngineAdapter(config.engine_executable, config.engine_fallback_executable)
    persistence = PersistenceService(store, config.export_dir)
    metrics = MetricsService()
    mapper = SymbolMapperService()
    classifier = EventClassifierService()
    sentiment = SentimentService()
    news = NewsIngestionService(
        config.news_seed_path,
        mapper,
        classifier,
        sentiment,
        config.news_feeds,
        config.max_news_articles,
        config.live_news_enabled,
    )
    signals = SignalService(config.market_symbols)
    portfolio = PortfolioService(config.market_symbols)
    risk = RiskService(config)
    gateway = OrderGateway(engine, risk, portfolio, metrics, persistence)
    strategy = StrategyService(gateway, portfolio, metrics, config.max_position_per_symbol)
    replay = ReplayService(persistence)
    simulator = SimulatorService(
        market_data,
        gateway,
        strategy,
        risk,
        portfolio,
        metrics,
        persistence,
        replay,
        news,
        signals,
        config.deterministic_seed,
    )
    return ServiceContainer(
        event_bus=event_bus,
        store=store,
        market_data=market_data,
        engine=engine,
        persistence=persistence,
        metrics=metrics,
        news=news,
        signals=signals,
        portfolio=portfolio,
        risk=risk,
        gateway=gateway,
        strategy=strategy,
        replay=replay,
        simulator=simulator,
    )


async def broadcast_loop(app: FastAPI) -> None:
    while True:
        payload = {"type": "dashboard", "data": app.state.services.simulator.dashboard_state().model_dump(mode="json")}
        await ws_manager.broadcast(payload)
        await asyncio.sleep(config.ws_broadcast_ms / 1000.0)


async def news_refresh_loop(app: FastAPI) -> None:
    while True:
        await app.state.services.simulator.refresh_news()
        await asyncio.sleep(config.news_refresh_seconds)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global services, broadcast_task, news_refresh_task
    services = build_services()
    await services.engine.start()
    app.state.services = services
    await services.simulator.refresh_news()
    broadcast_task = asyncio.create_task(broadcast_loop(app))
    news_refresh_task = asyncio.create_task(news_refresh_loop(app))
    try:
        yield
    finally:
        if broadcast_task:
            broadcast_task.cancel()
        if news_refresh_task:
            news_refresh_task.cancel()
        await services.engine.stop()
        services.store.close()


app = FastAPI(title=config.app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(market_router)
app.include_router(strategy_router)
app.include_router(risk_router)
app.include_router(portfolio_router)
app.include_router(metrics_router)
app.include_router(replay_router)
app.include_router(news_router)
app.include_router(signals_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await ws_manager.connect(websocket)
    try:
        if getattr(websocket.app.state, "services", None):
            await websocket.send_json({"type": "dashboard", "data": websocket.app.state.services.simulator.dashboard_state().model_dump(mode="json")})
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)
