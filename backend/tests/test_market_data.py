from pathlib import Path

from app.services.market_data_service import MarketDataService


def test_market_data_loads_and_generates_depth():
    data_dir = Path(__file__).resolve().parents[2] / "data"
    service = MarketDataService(data_dir=data_dir, symbols=["NIFTY", "RELIANCE"], seed=42)

    tick = service.next_tick("NIFTY")
    depth = service.synthetic_depth(tick)

    assert tick.symbol == "NIFTY"
    assert tick.last_price > 0
    assert len(depth.bids) == 5
    assert len(depth.asks) == 5
    assert depth.bids[0].price < depth.asks[0].price
