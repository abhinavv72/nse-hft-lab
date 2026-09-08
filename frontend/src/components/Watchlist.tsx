import type { MarketTick, SignalIdea } from "../types";

interface WatchlistProps {
  ideas: SignalIdea[];
  market: Record<string, MarketTick>;
  onSimulate: (symbol: string) => void;
  onRefresh: () => Promise<void>;
}

const label = (bias: SignalIdea["bias"]) => bias === "bullish" ? "Bullish watch" : bias === "bearish" ? "Bearish watch" : "Keep watching";

export default function Watchlist({ ideas, market, onSimulate, onRefresh }: WatchlistProps) {
  const ranked = ideas.slice(0, 5);
  return <main className="product-page">
    <section className="hero-copy">
      <p className="eyebrow">TOMORROW'S RESEARCH WATCHLIST</p>
      <h2>Understand the signal before you simulate a trade.</h2>
      <p>These are educational market-research signals based on available news, price movement, and volume—not buy or sell advice and never a return guarantee.</p>
      <button onClick={() => onRefresh()}>Refresh market research</button>
    </section>
    <section className="research-notice"><strong>How to read this:</strong> “Bullish watch” means the available inputs lean positive. Always read the reason and risk before making any personal investment decision.</section>
    <section className="watchlist-grid">
      {ranked.length === 0 && <p className="empty-state">No signals yet. Refresh research after the service connects.</p>}
      {ranked.map((idea, index) => {
        const tick = market[idea.symbol];
        return <article className="watch-card" key={idea.signal_id}>
          <div className="watch-card-top"><span className="rank">#{index + 1}</span><strong>{idea.symbol}</strong><span className={`bias ${idea.bias}`}>{label(idea.bias)}</span></div>
          <div className="watch-stats"><div><small>Last price</small><b>₹{(tick?.last_price ?? idea.last_price ?? 0).toLocaleString("en-IN", { maximumFractionDigits: 2 })}</b></div><div><small>Signal confidence</small><b>{idea.confidence.toFixed(0)}%</b></div><div><small>Move today</small><b>{(idea.change_pct ?? 0).toFixed(2)}%</b></div></div>
          <div className="reason-block"><small>Why this appears</small><p>{idea.reasons.slice(0, 2).join(" • ") || "Waiting for enough market context."}</p></div>
          <div className="risk-block"><small>What could go wrong</small><p>{idea.risks[0] || "Market conditions can change quickly; this is not a forecast."}</p></div>
          <button className="simulate-button" onClick={() => onSimulate(idea.symbol)}>Simulate {idea.symbol}</button>
        </article>;
      })}
    </section>
  </main>;
}
