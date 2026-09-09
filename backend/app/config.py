from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="NSE_HFT_", extra="ignore")

    app_name: str = "NSE-HFT-Lab"
    host: str = "0.0.0.0"
    port: int = 8000
    data_dir: Path = Field(default_factory=lambda: Path(__file__).resolve().parents[2] / "data")
    news_seed_path: Path = Field(default_factory=lambda: Path(__file__).resolve().parents[2] / "data" / "news_sample.csv")
    db_path: Path = Field(default_factory=lambda: Path(__file__).resolve().parents[1] / "runtime" / "lab.db")
    export_dir: Path = Field(default_factory=lambda: Path(__file__).resolve().parents[1] / "runtime" / "exports")
    engine_executable: Path = Field(default_factory=lambda: _engine_binary_path())
    engine_fallback_executable: Path = Field(default_factory=lambda: _engine_binary_path())
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    ws_broadcast_ms: int = 250
    live_price_refresh_seconds: int = 15
    deterministic_seed: int = 42
    max_order_qty: int = 500
    max_position_per_symbol: int = 2500
    max_daily_loss: float = 50000.0
    max_price_deviation_bps: float = 50.0
    stale_market_ms: int = 5000
    kill_switch_enabled: bool = False
    default_spread_bps: float = 8.0
    default_quote_qty: int = 25
    market_symbols: list[str] = ["NIFTY", "BANKNIFTY", "RELIANCE", "TCS", "INFY", "SBIN"]
    default_mode: str = "live"
    news_refresh_seconds: int = 300
    max_news_articles: int = 30
    live_news_enabled: bool = True
    live_prices_enabled: bool = True
    ai_hf_token: str = ""
    ai_model: str = "ProsusAI/finbert"
    ai_timeout_seconds: float = 12.0
    # Optional free IPO Guru key. Keep this server-side; never expose it to the browser.
    ipo_guru_api_key: str = ""
    news_feeds: list[str] = [
        "https://economictimes.indiatimes.com/markets/stocks/rssfeeds/2146842.cms",
        "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    ]
    symbol_yfinance_map: dict[str, str] = {
        "NIFTY": "^NSEI",
        "BANKNIFTY": "^NSEBANK",
        "RELIANCE": "RELIANCE.NS",
        "TCS": "TCS.NS",
        "INFY": "INFY.NS",
        "SBIN": "SBIN.NS",
    }


def _engine_binary_path() -> Path:
    root = Path(__file__).resolve().parents[2]
    candidates = [
        root / "engine" / "build" / "Release" / "nse_matching_engine.exe",
        root / "engine" / "build" / "nse_matching_engine.exe",
        root / "engine" / "build" / "nse_matching_engine",
    ]
    return next((path for path in candidates if path.exists()), candidates[0])


@lru_cache(maxsize=1)
def get_config() -> AppConfig:
    config = AppConfig()
    config.db_path.parent.mkdir(parents=True, exist_ok=True)
    config.export_dir.mkdir(parents=True, exist_ok=True)
    return config
