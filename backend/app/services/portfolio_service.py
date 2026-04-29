from __future__ import annotations

from collections import defaultdict

from app.core.models import PortfolioSnapshot, PositionSnapshot
from app.core.enums import Side


class PortfolioService:
    def __init__(self, symbols: list[str]) -> None:
        self.symbols = symbols
        self.positions: dict[str, PositionSnapshot] = {symbol: PositionSnapshot(symbol=symbol) for symbol in symbols}
        self.order_counts: dict[str, int] = defaultdict(int)
        self.fill_counts: dict[str, int] = defaultdict(int)

    def reset(self) -> None:
        self.positions = {symbol: PositionSnapshot(symbol=symbol) for symbol in self.symbols}
        self.order_counts.clear()
        self.fill_counts.clear()

    def register_order(self, symbol: str) -> None:
        self.order_counts[symbol] += 1

    def apply_fill(self, symbol: str, side: Side, qty: int, price: float) -> None:
        position = self.positions[symbol]
        signed_qty = qty if side == Side.BUY else -qty
        current_qty = position.net_qty
        new_qty = current_qty + signed_qty
        self.fill_counts[symbol] += 1
        position.trade_count += 1

        if current_qty == 0 or (current_qty > 0 and signed_qty > 0) or (current_qty < 0 and signed_qty < 0):
            total_cost = position.avg_price * abs(current_qty) + price * abs(signed_qty)
            position.net_qty = new_qty
            position.avg_price = total_cost / max(abs(new_qty), 1)
        else:
            closing_qty = min(abs(current_qty), abs(signed_qty))
            if current_qty > 0:
                position.realized_pnl += (price - position.avg_price) * closing_qty
            else:
                position.realized_pnl += (position.avg_price - price) * closing_qty
            if abs(signed_qty) > abs(current_qty):
                remaining_qty = abs(signed_qty) - abs(current_qty)
                position.net_qty = remaining_qty if signed_qty > 0 else -remaining_qty
                position.avg_price = price
            else:
                position.net_qty = new_qty
                if position.net_qty == 0:
                    position.avg_price = 0.0

        position.fill_ratio = round(self.fill_counts[symbol] / max(self.order_counts[symbol], 1), 3)

    def mark_market(self, symbol: str, price: float) -> None:
        position = self.positions[symbol]
        position.mark_price = price
        if position.net_qty > 0:
            position.unrealized_pnl = (price - position.avg_price) * position.net_qty
        elif position.net_qty < 0:
            position.unrealized_pnl = (position.avg_price - price) * abs(position.net_qty)
        else:
            position.unrealized_pnl = 0.0

    def snapshot(self) -> PortfolioSnapshot:
        positions = [self.positions[symbol] for symbol in self.symbols]
        realized = sum(position.realized_pnl for position in positions)
        unrealized = sum(position.unrealized_pnl for position in positions)
        total_trades = sum(position.trade_count for position in positions)
        return PortfolioSnapshot(
            positions=positions,
            realized_pnl=round(realized, 2),
            unrealized_pnl=round(unrealized, 2),
            total_pnl=round(realized + unrealized, 2),
            total_trades=total_trades,
        )
