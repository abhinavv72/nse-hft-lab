import type { MarketTick } from "../types";

interface MarketWatchProps {
  market: Record<string, MarketTick>;
  selectedSymbol: string;
  onSelectSymbol: (symbol: string) => Promise<void>;
}

export default function MarketWatch({ market, selectedSymbol, onSelectSymbol }: MarketWatchProps) {
  return (
    <div>
      <div className="panel-header">
        <h2>Market Watch</h2>
        <span>{Object.keys(market).length} symbols</span>
      </div>
      <div className="table-grid">
        <div className="row head">
          <span>Symbol</span>
          <span>Last</span>
          <span>Spread</span>
          <span>Vol Proxy</span>
        </div>
        {Object.values(market).map((tick) => (
          <button
            key={tick.symbol}
            className={`row button-row ${selectedSymbol === tick.symbol ? "selected" : ""}`}
            onClick={() => onSelectSymbol(tick.symbol)}
          >
            <span>{tick.symbol}</span>
            <span>{tick.last_price.toFixed(2)}</span>
            <span>{tick.spread.toFixed(2)}</span>
            <span>{tick.volume.toLocaleString()}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
