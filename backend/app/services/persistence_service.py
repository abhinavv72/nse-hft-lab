from __future__ import annotations

import csv
import json
from pathlib import Path

from app.adapters.duckdb_adapter import LocalAnalyticsStore
from app.core.clock import utc_now_iso
from app.core.models import LogEvent, NewsArticle, OrderRecord, PortfolioSnapshot, SignalIdea, TradeRecord


class PersistenceService:
    def __init__(self, store: LocalAnalyticsStore, export_dir: Path) -> None:
        self.store = store
        self.export_dir = export_dir

    async def persist_tick(self, session_id: str, tick: dict) -> None:
        self.store.connection.execute(
            "INSERT INTO ticks VALUES (?, ?, ?, ?, ?, ?, ?)",
            (session_id, tick["timestamp"], tick["symbol"], tick["last_price"], tick["mid_price"], tick["volume"], tick["volatility"]),
        )
        self.store.connection.commit()

    async def persist_order(self, session_id: str, order: OrderRecord) -> None:
        self.store.connection.execute(
            "INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                session_id,
                order.timestamp,
                order.order_id,
                order.symbol,
                order.side.value,
                order.order_type.value,
                order.price,
                order.qty,
                order.remaining_qty,
                order.filled_qty,
                order.status.value,
                order.owner,
                order.strategy_id,
                order.reject_reason,
            ),
        )
        self.store.connection.commit()

    async def persist_fill(self, session_id: str, fill: TradeRecord) -> None:
        self.store.connection.execute(
            "INSERT INTO fills VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                session_id,
                fill.timestamp,
                fill.trade_id,
                fill.symbol,
                fill.price,
                fill.qty,
                fill.taker_order_id,
                fill.maker_order_id,
                fill.aggressor_side.value,
                fill.source_owner,
            ),
        )
        self.store.connection.commit()

    async def persist_portfolio(self, session_id: str, portfolio: PortfolioSnapshot) -> None:
        timestamp = utc_now_iso()
        for position in portfolio.positions:
            self.store.connection.execute(
                "INSERT INTO pnl_snapshots VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    session_id,
                    timestamp,
                    position.symbol,
                    position.net_qty,
                    position.avg_price,
                    position.realized_pnl,
                    position.unrealized_pnl,
                    position.mark_price,
                    position.trade_count,
                ),
            )
        self.store.connection.commit()

    async def persist_latency(self, session_id: str, category: str, value_ms: float, timestamp: str) -> None:
        self.store.connection.execute(
            "INSERT INTO latency_samples VALUES (?, ?, ?, ?)",
            (session_id, timestamp, category, value_ms),
        )
        self.store.connection.commit()

    async def persist_log(self, session_id: str, log_event: LogEvent) -> None:
        self.store.connection.execute(
            "INSERT INTO logs VALUES (?, ?, ?, ?, ?, ?)",
            (
                session_id,
                log_event.timestamp,
                log_event.level,
                log_event.category,
                log_event.message,
                json.dumps(log_event.data),
            ),
        )
        self.store.connection.commit()
        print(json.dumps(log_event.model_dump()))

    async def persist_news(self, session_id: str, article: NewsArticle) -> None:
        self.store.connection.execute(
            "INSERT INTO news_articles VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                session_id,
                article.article_id,
                article.timestamp,
                article.source,
                article.headline,
                article.summary,
                article.url,
                json.dumps(article.symbols),
                article.sentiment,
                article.impact_score,
                json.dumps(article.tags),
            ),
        )
        self.store.connection.commit()

    async def replace_signals(self, session_id: str, signals: list[SignalIdea]) -> None:
        self.store.connection.execute("DELETE FROM signal_ideas WHERE session_id = ?", (session_id,))
        for signal in signals:
            self.store.connection.execute(
                "INSERT INTO signal_ideas VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    session_id,
                    signal.signal_id,
                    signal.timestamp,
                    signal.symbol,
                    signal.bias,
                    signal.confidence,
                    signal.score,
                    signal.horizon,
                    signal.last_price,
                    signal.change_pct,
                    json.dumps(signal.reasons),
                    json.dumps(signal.risks),
                    json.dumps(signal.related_articles),
                ),
            )
        self.store.connection.commit()

    def fetch_ticks(self, session_id: str) -> list[dict]:
        cursor = self.store.connection.execute(
            "SELECT timestamp, symbol, last_price, mid_price, volume, volatility FROM ticks WHERE session_id = ? ORDER BY timestamp",
            (session_id,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def list_sessions(self) -> list[str]:
        cursor = self.store.connection.execute("SELECT DISTINCT session_id FROM ticks ORDER BY session_id DESC")
        return [row[0] for row in cursor.fetchall()]

    def export_session(self, session_id: str) -> dict[str, str]:
        session_dir = self.export_dir / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        for table in ("ticks", "orders", "fills", "pnl_snapshots", "latency_samples", "logs", "news_articles", "signal_ideas"):
            query = self.store.connection.execute(f"SELECT * FROM {table} WHERE session_id = ?", (session_id,))
            rows = query.fetchall()
            file_path = session_dir / f"{table}.csv"
            with file_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.writer(handle)
                writer.writerow([column[0] for column in query.description])
                for row in rows:
                    writer.writerow(list(row))
        return {"session_id": session_id, "export_dir": str(session_dir)}
