from __future__ import annotations

import csv
import sqlite3
from pathlib import Path


class LocalAnalyticsStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(self.db_path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._init_schema()

    @property
    def connection(self) -> sqlite3.Connection:
        return self._connection

    def _init_schema(self) -> None:
        cursor = self._connection.cursor()
        cursor.executescript(
            """
            CREATE TABLE IF NOT EXISTS ticks (
                session_id TEXT,
                timestamp TEXT,
                symbol TEXT,
                last_price REAL,
                mid_price REAL,
                volume INTEGER,
                volatility REAL
            );
            CREATE TABLE IF NOT EXISTS orders (
                session_id TEXT,
                timestamp TEXT,
                order_id TEXT,
                symbol TEXT,
                side TEXT,
                order_type TEXT,
                price REAL,
                qty INTEGER,
                remaining_qty INTEGER,
                filled_qty INTEGER,
                status TEXT,
                owner TEXT,
                strategy_id TEXT,
                reject_reason TEXT
            );
            CREATE TABLE IF NOT EXISTS fills (
                session_id TEXT,
                timestamp TEXT,
                trade_id TEXT,
                symbol TEXT,
                price REAL,
                qty INTEGER,
                taker_order_id TEXT,
                maker_order_id TEXT,
                aggressor_side TEXT,
                source_owner TEXT
            );
            CREATE TABLE IF NOT EXISTS pnl_snapshots (
                session_id TEXT,
                timestamp TEXT,
                symbol TEXT,
                net_qty INTEGER,
                avg_price REAL,
                realized_pnl REAL,
                unrealized_pnl REAL,
                mark_price REAL,
                trade_count INTEGER
            );
            CREATE TABLE IF NOT EXISTS latency_samples (
                session_id TEXT,
                timestamp TEXT,
                category TEXT,
                value_ms REAL
            );
            CREATE TABLE IF NOT EXISTS logs (
                session_id TEXT,
                timestamp TEXT,
                level TEXT,
                category TEXT,
                message TEXT,
                data TEXT
            );
            CREATE TABLE IF NOT EXISTS news_articles (
                session_id TEXT,
                article_id TEXT,
                timestamp TEXT,
                source TEXT,
                headline TEXT,
                summary TEXT,
                url TEXT,
                symbols TEXT,
                sentiment TEXT,
                impact_score REAL,
                tags TEXT
            );
            CREATE TABLE IF NOT EXISTS signal_ideas (
                session_id TEXT,
                signal_id TEXT,
                timestamp TEXT,
                symbol TEXT,
                bias TEXT,
                confidence REAL,
                score REAL,
                horizon TEXT,
                last_price REAL,
                change_pct REAL,
                reasons TEXT,
                risks TEXT,
                related_articles TEXT
            );
            """
        )
        self._connection.commit()

    def export_table_to_csv(self, table: str, export_path: Path) -> None:
        cursor = self._connection.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()
        export_path.parent.mkdir(parents=True, exist_ok=True)
        with export_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow([column[0] for column in cursor.description])
            for row in rows:
                writer.writerow(list(row))

    def close(self) -> None:
        self._connection.close()
