import { useMemo } from "react";

import type { MarketTick, NewsArticle, SignalIdea } from "../types";

interface StockDetailProps {
  idea: SignalIdea;
  tick?: MarketTick;
  ticks: MarketTick[];
  articles: NewsArticle[];
  onClose: () => void;
  onSimulate: () => void;
}

function PriceTrail({ ticks }: { ticks: MarketTick[] }) {
  const points = useMemo(() => {
    if (ticks.length < 2) return "";
    const values = ticks.map((point) => point.last_price);
    const min = Math.min(...values);
    const max = Math.max(...values);
    const range = max - min || 1;
    return values.map((value, index) => `${(index / (values.length - 1)) * 100},${92 - ((value - min) / range) * 76}`).join(" ");
  }, [ticks]);
  const move = ticks.length > 1 ? ((ticks[ticks.length - 1].last_price - ticks[0].last_price) / ticks[0].last_price) * 100 : 0;
  return <div className="price-trail"><div className="chart-topline"><strong>In-session price trail</strong><span className={move >= 0 ? "buy-text" : "sell-text"}>{ticks.length > 1 ? `${move >= 0 ? "+" : ""}${move.toFixed(2)}%` : "Collecting data"}</span></div><svg viewBox="0 0 100 100" role="img" aria-label="Recent in-session price trail"><line x1="0" x2="100" y1="25" y2="25" /><line x1="0" x2="100" y1="50" y2="50" /><line x1="0" x2="100" y1="75" y2="75" />{points ? <polyline points={points} /> : <text x="50" y="52" textAnchor="middle">Waiting for price points</text>}</svg><small>Built from this session’s streamed market snapshots; not a long-term historical chart.</small></div>;
}

export default function StockDetail({ idea, tick, ticks, articles, onClose, onSimulate }: StockDetailProps) {
  const related = articles.filter((article) => article.symbols.includes(idea.symbol)).slice(0, 4);
  const setup = Math.max(0, Math.min(100, Math.round(50 + idea.score)));
  return <section className="stock-detail" aria-label={`${idea.symbol} research detail`}>
    <div className="detail-heading"><div><p className="eyebrow">STOCK RESEARCH DETAIL</p><h2>{idea.symbol} <span className={`bias ${idea.bias}`}>{idea.bias === "bullish" ? "Bullish watch" : idea.bias === "bearish" ? "Bearish watch" : "Keep watching"}</span></h2><p className="subtle">Last price ₹{(tick?.last_price ?? idea.last_price ?? 0).toLocaleString("en-IN", { maximumFractionDigits: 2 })} · updated from the current session</p></div><button className="muted" onClick={onClose}>Close</button></div>
    <div className="detail-grid"><PriceTrail ticks={ticks} /><div className="setup-score"><small>Opportunity score</small><strong>{setup}<em>/100</em></strong><p>Score combines the current research inputs. It is not a price target or a guarantee.</p><div className="score-bar"><span style={{ width: `${setup}%` }} /></div></div></div>
    <div className="detail-grid three"><article><h3>Why it appears</h3>{idea.reasons.length ? <ul>{idea.reasons.map((reason) => <li key={reason}>{reason}</li>)}</ul> : <p>No supporting inputs yet.</p>}</article><article><h3>Risk to review</h3>{idea.risks.length ? <ul>{idea.risks.map((risk) => <li key={risk}>{risk}</li>)}</ul> : <p>Market conditions, liquidity and news can change quickly.</p>}</article><article><h3>Before simulation</h3><p>Check price movement, the news sources below, and your own risk tolerance. A strong setup can still fail.</p><button onClick={onSimulate}>Open {idea.symbol} simulator</button></article></div>
    <article className="detail-news"><h3>News evidence</h3>{related.length ? related.map((article) => <div className="news-evidence" key={article.article_id}><strong>{article.headline}</strong><span>{article.source} · {article.analysis_source === "finbert" ? "AI sentiment" : "rule-based sentiment"}</span>{article.url && <a href={article.url} target="_blank" rel="noreferrer">Open source</a>}</div>) : <p className="empty-state">No mapped news articles for this stock in the current feed.</p>}</article>
  </section>;
}
