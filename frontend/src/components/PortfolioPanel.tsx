import type { PortfolioSnapshot } from "../types";

interface PortfolioPanelProps {
  portfolio?: PortfolioSnapshot;
}

export default function PortfolioPanel({ portfolio }: PortfolioPanelProps) {
  return (
    <div>
      <div className="panel-header">
        <h2>Portfolio</h2>
        <span>Total PnL {portfolio?.total_pnl.toFixed(2) ?? "0.00"}</span>
      </div>
      <div className="table-grid compact">
        <div className="row head">
          <span>Symbol</span>
          <span>Pos</span>
          <span>Avg Px</span>
          <span>Unreal</span>
          <span>Real</span>
        </div>
        {(portfolio?.positions ?? []).map((position) => (
          <div className="row" key={position.symbol}>
            <span>{position.symbol}</span>
            <span>{position.net_qty}</span>
            <span>{position.avg_price.toFixed(2)}</span>
            <span>{position.unrealized_pnl.toFixed(2)}</span>
            <span>{position.realized_pnl.toFixed(2)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
