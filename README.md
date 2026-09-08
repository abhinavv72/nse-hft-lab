# NSE-HFT-Lab

Local-first HFT-style trading simulator for Indian markets with a C++ matching engine, FastAPI control plane, SQLite persistence, and a live React dashboard.

> **Educational simulation only.** This project does not connect to a broker, execute real orders, or provide investment advice. Market depth and execution are simulated; live price and news sources can be unavailable or delayed.

News is ranked by deterministic rules by default. Optionally set `NSE_HFT_AI_HF_TOKEN` to a user-owned Hugging Face Inference Providers token to use the open-source `ProsusAI/finbert` financial-sentiment model; articles visibly identify whether FinBERT or the rules fallback produced the analysis.

## What It Does

- Replays bundled NSE-style seed data for `NIFTY`, `BANKNIFTY`, `RELIANCE`, `TCS`, `INFY`, and `SBIN`
- Generates synthetic top-of-book plus depth around seeded prices
- Runs a local in-memory matching engine with price-time priority
- Applies pre-trade risk checks before strategy orders reach the engine
- Tracks positions, realized/unrealized PnL, trade counts, and fill ratios
- Ingests seeded and optional live free-market headlines into a news feed
- Scores symbols into bullish, bearish, or neutral daily trade ideas with confidence and reasons
- Streams dashboard state over WebSockets
- Persists ticks, orders, fills, PnL snapshots, latency samples, and logs locally
- Supports session export and replay of recent recorded sessions

## Architecture

### Runtime shape

- `engine/`
  - C++20 matching engine executable
  - per-symbol order books
  - FIFO within price level
  - limit, market, cancel, partial fills, snapshots
- `backend/`
  - FastAPI REST API and WebSocket broadcaster
  - market simulator and replay mode
  - strategy engine with market maker and mean reversion
  - risk service, portfolio service, metrics service
  - SQLite-backed persistence
- `frontend/`
  - React + TypeScript + Vite trading dashboard
  - market watch, order book, strategy control, top ideas, news feed, blotter, risk, portfolio, metrics, logs
- `data/`
  - local seed CSVs that can later be replaced with official NSE/bhavcopy-derived files

### Data flow

1. Seed CSV rows are replayed into `MarketTick` objects.
2. The simulator generates synthetic bid/ask depth around the seed price.
3. Synthetic market liquidity is submitted into the local matching engine.
4. Strategies react to ticks and submit orders through the risk gateway.
5. The engine emits fills and snapshots.
6. News headlines are normalized, mapped to symbols, and scored into daily trade ideas.
7. Portfolio, metrics, signals, and persistence update.
8. FastAPI broadcasts a live dashboard snapshot over WebSocket.

## Project Structure

```text
nse-hft-lab/
  README.md
  docker-compose.yml
  .env.example
  scripts/
  data/
  backend/
  engine/
  frontend/
```

## Local Windows Setup

### Prerequisites

- Windows 10/11
- Python 3.11+
- Node.js 20+
- CMake 3.20+
- Visual Studio Build Tools with C++ workload

### Exact startup steps

```powershell
cd C:\Users\KIIT\OneDrive\Desktop\projects\nse-hft-lab
.\scripts\setup.ps1
```

In terminal 1:

```powershell
cd C:\Users\KIIT\OneDrive\Desktop\projects\nse-hft-lab
.\scripts\run_backend.ps1
```

In terminal 2:

```powershell
cd C:\Users\KIIT\OneDrive\Desktop\projects\nse-hft-lab
.\scripts\run_frontend.ps1
```

### URLs

- Backend: [http://localhost:8000](http://localhost:8000)
- Frontend: [http://localhost:5173](http://localhost:5173)
- WebSocket: `ws://localhost:8000/ws`

## Optional Docker Run

```powershell
docker compose up --build
```

## Public Demo Deployment

The production Docker image builds the React app and serves it through FastAPI, so the dashboard, REST API, and WebSocket share one HTTPS origin. This avoids public CORS and WebSocket URL configuration issues.

For a free portfolio demo, deploy `backend/Dockerfile` as a Docker web service with the repository root as the build context and `/health` as its health-check path. Free hosts use temporary storage, so sessions and local SQLite data reset after a restart; this is expected for demo mode.

## API Overview

- `POST /api/market/start`
- `POST /api/market/stop`
- `POST /api/market/reset`
- `POST /api/market/volatility-spike`
- `POST /api/market/select-symbol`
- `GET /api/market/state`
- `GET /api/strategy`
- `POST /api/strategy/start/{strategy_id}`
- `POST /api/strategy/stop/{strategy_id}`
- `GET /api/risk`
- `POST /api/risk/kill-switch`
- `GET /api/portfolio`
- `GET /api/metrics`
- `GET /api/news`
- `POST /api/news/refresh`
- `GET /api/signals`
- `GET /api/replay/sessions`
- `POST /api/replay/start`
- `POST /api/replay/export`

## How To Demo

1. Start backend and frontend.
2. Open the dashboard and confirm market watch is live.
3. Click `Start 5x`.
4. Watch the order book update as synthetic depth refreshes.
5. Start `market_maker`.
6. Start `mean_reversion`.
7. Show orders and fills entering the blotter.
8. Trigger `Vol Spike` and show strategy reaction.
9. Trigger the kill switch from the risk panel and show order blocking.
10. Show the `Top Ideas` and `News Feed` panels updating with bullish/bearish reasoning.
11. Export the session.
12. Replay the latest session.

## 5-Minute Demo Script

1. "This is a local-first Indian market trading lab. No broker APIs, no API keys, no cloud dependencies."
2. "The C++ engine maintains per-symbol order books with FIFO price-time priority."
3. "The Python control plane handles seeded market replay, synthetic liquidity, strategies, risk, persistence, and WebSocket fanout."
4. "The React UI is a live dashboard for market, execution, risk, PnL, and latency."
5. "I also layered in a free news-to-signal engine that ranks today's bullish and bearish ideas with explainable reasons."
6. "I can inject a volatility spike, toggle a kill switch, export a session, and replay it locally."

## Interview Talking Points

- Clean separation between the latency-sensitive matching path and the higher-level orchestration path
- Real order lifecycle with partial fills, cancels, snapshots, and PnL updates
- Risk gateway modeled as a synchronous pre-trade control point
- Deterministic local replay using bundled seed data
- Free news-ingestion and rules-based signal scoring layer built to stay local-first, explainable, and upgradeable later
- Architecture is designed to swap sample data for official NSE historical files with minimal code changes
- Engine transport uses a subprocess protocol today but the adapter boundary is clean enough to upgrade to `pybind11` later

## Simplifications vs Production

### Simplified here

- Synthetic depth instead of real NSE L2/L3 feeds
- Python orchestrates strategies and UI fanout
- Subprocess protocol instead of in-process native bindings
- SQLite instead of a higher-throughput event store
- Snapshot broadcast instead of fine-grained event diff streaming
- Rules-based idea scoring instead of a larger NLP or ML model

### Production-grade version would

- move more execution-critical logic into C++ or colocated services
- use binary market data protocols and explicit venue microstructure models
- introduce a lower-latency transport than subprocess stdio
- add better strategy scheduling, backtesting, and event sourcing
- upgrade the news layer to stronger entity resolution, better event extraction, and formal signal backtesting
- support multi-venue routing, smart order routing, and more realistic network latency models

## Likely Issues And Fixes

- Python package install blocked: rerun `.\scripts\setup.ps1` with internet access enabled
- C++ engine build fails on Windows SDK permissions: run PowerShell with the Build Tools environment available
- Frontend `npm` issues on PowerShell: use `npm.cmd` directly, which the scripts already do
- Backend starts without the engine executable: rebuild with `cmake --build engine/build --config Release`

## Tests

### Engine

```powershell
cd .\engine
cmake -S . -B build
cmake --build build --config Release
.\build\Release\test_matching_engine.exe
```

### Backend

```powershell
cd .\backend
python -m pytest
```

## Resume Bullet Ideas

- Built a local-first HFT-style simulator for Indian markets with a C++20 matching engine, FastAPI orchestration layer, SQLite event persistence, and a live React dashboard
- Implemented price-time-priority order books with partial fills, cancels, top-of-book snapshots, and a clean subprocess adapter boundary for later native binding upgrades
- Designed a deterministic market replay and synthetic depth generator around bundled NSE-style seed data, with risk controls, strategy execution, PnL tracking, session export, and replay
- Exposed live execution, risk, latency, and portfolio telemetry over WebSockets in a production-style trading dashboard

## Current Validation Status In This Environment

- C++ engine configured, compiled, and unit-tested successfully on Windows
- Backend tests pass with `7 passed`
- Frontend production build passes with `npm.cmd run build`
- News and signals APIs are included in the backend smoke coverage
