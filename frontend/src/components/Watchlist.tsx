import { useMemo, useState } from "react";

import { api } from "../api/client";
import type { MarketTick, NewsArticle, NseQuote, SignalIdea } from "../types";
import type { MarketHistory } from "../hooks/useMarketStream";
import StockDetail from "./StockDetail";

interface WatchlistProps {
  ideas: SignalIdea[];
  market: Record<string, MarketTick>;
  history: MarketHistory;
  articles: NewsArticle[];
  onSimulate: (symbol: string) => void;
  onRefresh: () => Promise<void>;
}

const label = (bias: SignalIdea["bias"]) => bias === "bullish" ? "Bullish watch" : bias === "bearish" ? "Bearish watch" : "Keep watching";

export default function Watchlist({ ideas, market, history, articles, onSimulate, onRefresh }: WatchlistProps) {
  const [query, setQuery] = useState("");
  const [biasFilter, setBiasFilter] = useState<"all" | SignalIdea["bias"]>("all");
  const [selectedSymbol, setSelectedSymbol] = useState<string | null>(null);
  const [universalSymbol, setUniversalSymbol] = useState("");
  const [universalQuote, setUniversalQuote] = useState<NseQuote | null>(null);
  const [quoteState, setQuoteState] = useState<"idle" | "loading" | "error">("idle");
  const ranked = useMemo(() => ideas
    .filter((idea) => idea.symbol.toLowerCase().includes(query.toLowerCase()))
    .filter((idea) => biasFilter === "all" || idea.bias === biasFilter)
    .slice(0, 8), [ideas, query, biasFilter]);
  const selectedIdea = ideas.find((idea) => idea.symbol === selectedSymbol) ?? null;
  const searchNse = async () => {
    if (!universalSymbol.trim()) return;
    setQuoteState("loading"); setUniversalQuote(null);
    try { setUniversalQuote(await api.getNseQuote(universalSymbol)); setQuoteState("idle"); }
    catch { setQuoteState("error"); }
  };
  return <main className="product-page">
    <section className="hero-copy">
      <p className="eyebrow">TOMORROW'S RESEARCH WATCHLIST</p>
      <h2>Understand the signal before you simulate a trade.</h2>
      <p>These are educational market-research signals based on available news, price movement, and volume—not buy or sell advice and never a return guarantee.</p>
      <button onClick={() => onRefresh()}>Refresh market research</button>
    </section>
    <section className="research-notice"><strong>How to read this:</strong> “Bullish watch” means the available inputs lean positive. Always read the reason and risk before making any personal investment decision.</section>
    <section className="universal-search" aria-label="Universal NSE stock search">
      <div><p className="eyebrow">UNIVERSAL NSE SEARCH</p><h2>Search any NSE stock.</h2><p>Enter a trading symbol such as ESDS, HDFCBANK, TATAMOTORS, or INFY.</p></div>
      <div className="search-row"><input value={universalSymbol} onChange={(event) => setUniversalSymbol(event.target.value.toUpperCase())} onKeyDown={(event) => { if (event.key === "Enter") void searchNse(); }} placeholder="Enter NSE symbol" /><button onClick={() => void searchNse()} disabled={quoteState === "loading"}>{quoteState === "loading" ? "Searching…" : "Search stock"}</button></div>
      {quoteState === "error" && <p className="empty-state">Stock was not found or its quote is temporarily unavailable. Search using its NSE trading symbol.</p>}
      {universalQuote && <article className="universal-quote"><div className="watch-card-top"><strong>{universalQuote.symbol}</strong><span className="pill ok">{universalQuote.market_status}</span></div><div className="watch-stats"><div><small>Last available price</small><b>₹{universalQuote.last_price.toLocaleString("en-IN", { maximumFractionDigits: 2 })}</b></div><div><small>Open</small><b>₹{universalQuote.open.toLocaleString("en-IN", { maximumFractionDigits: 2 })}</b></div><div><small>Day high</small><b>₹{universalQuote.high.toLocaleString("en-IN", { maximumFractionDigits: 2 })}</b></div><div><small>Day low</small><b>₹{universalQuote.low.toLocaleString("en-IN", { maximumFractionDigits: 2 })}</b></div><div><small>Volume</small><b>{universalQuote.volume.toLocaleString("en-IN")}</b></div></div><p className="subtle">Source: {universalQuote.source} · The stock is available for research; the simulator basket remains unchanged.</p></article>}
    </section>
    <section className="watchlist-tools" aria-label="Watchlist filters">
      <label>Find a stock<input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search symbol, e.g. INFY" /></label>
      <label>Signal type<select value={biasFilter} onChange={(event) => setBiasFilter(event.target.value as typeof biasFilter)}><option value="all">All signals</option><option value="bullish">Bullish watch</option><option value="neutral">Keep watching</option><option value="bearish">Bearish watch</option></select></label>
      <span>{ranked.length} research signals shown</span>
    </section>
    <section className="watchlist-grid">
      {ranked.length === 0 && <p className="empty-state">No signals yet. Refresh research after the service connects.</p>}
      {ranked.map((idea, index) => {
        const tick = market[idea.symbol];
        return <article className="watch-card" key={idea.signal_id}>
          <div className="watch-card-top"><span className="rank">#{index + 1}</span><strong>{idea.symbol}</strong><span className={`bias ${idea.bias}`}>{label(idea.bias)}</span></div>
          <div className="watch-stats"><div><small>Last price</small><b>₹{(tick?.last_price ?? idea.last_price ?? 0).toLocaleString("en-IN", { maximumFractionDigits: 2 })}</b></div><div><small>Signal confidence</small><b>{idea.confidence.toFixed(0)}%</b></div><div><small>Move today</small><b>{(idea.change_pct ?? 0).toFixed(2)}%</b></div></div>
          <div className="reason-block"><small>Why this appears</small><p>{idea.reasons.slice(0, 2).join(" • ") || "Waiting for enough market context."}</p></div>
          <div className="risk-block"><small>What could go wrong</small><p>{idea.risks[0] || "Market conditions can change quickly; this is not a forecast."}</p></div>
          <div className="card-actions"><button className="muted" onClick={() => setSelectedSymbol(idea.symbol)}>View research</button><button className="simulate-button" onClick={() => onSimulate(idea.symbol)}>Simulate</button></div>
        </article>;
      })}
    </section>
    {selectedIdea && <StockDetail idea={selectedIdea} tick={market[selectedIdea.symbol]} ticks={history[selectedIdea.symbol] ?? []} articles={articles} onClose={() => setSelectedSymbol(null)} onSimulate={() => onSimulate(selectedIdea.symbol)} />}
  </main>;
}
