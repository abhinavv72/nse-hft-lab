from app.config import AppConfig
from app.core.enums import Side
from app.core.models import OrderRequest, PortfolioSnapshot, PositionSnapshot
from app.services.risk_service import RiskService


def test_risk_rejects_large_orders():
    config = AppConfig(max_order_qty=10)
    risk = RiskService(config)
    risk.update_market_timestamp("NIFTY")
    portfolio = PortfolioSnapshot(positions=[PositionSnapshot(symbol="NIFTY")], total_pnl=0.0)

    approved, reason = risk.check_order(
        OrderRequest(symbol="NIFTY", side=Side.BUY, price=22000.0, qty=50, owner="test"),
        market_price=22000.0,
        portfolio=portfolio,
    )

    assert approved is False
    assert reason == "Order quantity exceeds limit"


def test_risk_rejects_when_kill_switch_is_enabled():
    config = AppConfig(kill_switch_enabled=True)
    risk = RiskService(config)
    risk.update_market_timestamp("NIFTY")
    portfolio = PortfolioSnapshot(positions=[PositionSnapshot(symbol="NIFTY")], total_pnl=0.0)

    approved, reason = risk.check_order(
        OrderRequest(symbol="NIFTY", side=Side.SELL, price=22010.0, qty=5, owner="test"),
        market_price=22000.0,
        portfolio=portfolio,
    )

    assert approved is False
    assert reason == "Kill switch active"
