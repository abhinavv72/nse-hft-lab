from app.core.enums import Side
from app.services.portfolio_service import PortfolioService


def test_portfolio_updates_realized_and_unrealized_pnl():
    service = PortfolioService(["RELIANCE"])
    service.register_order("RELIANCE")
    service.apply_fill("RELIANCE", Side.BUY, qty=10, price=100.0)
    service.mark_market("RELIANCE", 104.0)

    snapshot = service.snapshot()
    position = snapshot.positions[0]
    assert position.net_qty == 10
    assert position.unrealized_pnl == 40.0

    service.register_order("RELIANCE")
    service.apply_fill("RELIANCE", Side.SELL, qty=4, price=105.0)
    snapshot = service.snapshot()
    position = snapshot.positions[0]
    assert position.net_qty == 6
    assert position.realized_pnl == 20.0
