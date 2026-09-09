import { useEffect, useMemo, useState } from "react";

import { api } from "../api/client";
import type { IpoIssue, NewsArticle } from "../types";

function upperBand(issue: IpoIssue) {
  const values = issue.price_band.match(/\d+(?:\.\d+)?/g)?.map(Number) ?? [];
  return values.length ? Math.max(...values) : null;
}

function applicationAmount(issue: IpoIssue) {
  const band = upperBand(issue);
  return band && issue.lot_size ? band * issue.lot_size : null;
}

function oneLotGmpGain(issue: IpoIssue) {
  return issue.lot_size && issue.gmp !== null ? issue.lot_size * issue.gmp : null;
}

function formatShares(value: IpoIssue["issue_size_shares"]) {
  const numeric = Number(value);
  return Number.isFinite(numeric) && numeric > 0 ? numeric.toLocaleString("en-IN") : "Not published";
}

export default function IpoResearch({ articles }: { articles: NewsArticle[] }) {
  const [issues, setIssues] = useState<IpoIssue[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selected, setSelected] = useState<IpoIssue | null>(null);
  const [gmp, setGmp] = useState("");

  const load = async () => {
    setLoading(true); setError("");
    try { const response = await api.getCurrentIpos(); setIssues(response.issues); }
    catch { setError("NSE’s official current-issue feed is temporarily unavailable. Try refresh again shortly."); }
    finally { setLoading(false); }
  };
  useEffect(() => { void load(); }, []);

  const ipoArticles = useMemo(() => articles.filter((article) => /\bipo\b|anchor|listing/i.test(`${article.headline} ${article.summary}`)).slice(0, 6), [articles]);
  const band = selected ? upperBand(selected) : null;
  const gmpNumber = Number(gmp);
  const scenarioPercent = band && Number.isFinite(gmpNumber) && gmpNumber >= 0 ? (gmpNumber / band) * 100 : null;
  const lotCost = selected && band && selected.lot_size ? band * selected.lot_size : null;
  const lotProfit = selected?.lot_size && Number.isFinite(gmpNumber) && gmpNumber >= 0 ? selected.lot_size * gmpNumber : null;

  return <main className="product-page">
    <section className="hero-copy"><p className="eyebrow">LIVE NSE IPO TRACKER</p><h2>Current IPO GMP and one-lot opportunity list.</h2><p>IPO details come from NSE. GMP, lot size, and timestamps come from IPO Guru.</p><button onClick={() => void load()} disabled={loading}>{loading ? "Refreshing live data…" : "Refresh live data"}</button></section>
    {error && <p className="empty-state">{error}</p>}
    <section className="ipo-grid">
      {issues.map((issue) => <article className="ipo-card" key={`${issue.symbol}-${issue.company_name}`}><div className="watch-card-top"><strong>{issue.company_name}</strong><span className="pill ok">{issue.status}</span></div><span className="subtle">{issue.symbol || "Symbol pending"} · {issue.series || "IPO"}</span><div className="ipo-facts"><div><small>Open</small><b>{issue.open_date || "Not published"}</b></div><div><small>Close</small><b>{issue.close_date || "Not published"}</b></div><div><small>Price band</small><b>{issue.price_band}</b></div><div><small>Subscription</small><b>{issue.subscription_times === null ? "Awaiting data" : `${issue.subscription_times.toFixed(2)}×`}</b></div><div><small>Lot size</small><b>{issue.lot_size ? `${issue.lot_size} shares` : "Awaiting provider"}</b></div><div><small>Application amount</small><b>{applicationAmount(issue) === null ? "Awaiting provider" : `₹${applicationAmount(issue)?.toLocaleString("en-IN")}`}</b></div><div><small>Live GMP</small><b>{issue.gmp === null ? "Unavailable" : `₹${issue.gmp}`}</b>{issue.gmp_updated_at && <span className="subtle">{issue.gmp_source} · {issue.gmp_updated_at}</span>}</div><div className="ipo-profit"><small>One-lot GMP gain</small><strong>{oneLotGmpGain(issue) === null ? "Awaiting live GMP" : `₹${oneLotGmpGain(issue)?.toLocaleString("en-IN")}`}</strong></div></div><div className="card-actions"><a className="button-link muted" href={issue.official_url} target="_blank" rel="noreferrer">NSE issue page</a><button onClick={() => { setSelected(issue); setGmp(issue.gmp === null ? "" : String(issue.gmp)); }}>View one-lot breakdown</button></div></article>)}
      {!loading && !error && issues.length === 0 && <p className="empty-state">NSE currently reports no active IPO issues.</p>}
    </section>
    {selected && <section className="ipo-scenario"><div className="detail-heading"><div><p className="eyebrow">ONE-LOT BREAKDOWN</p><h2>{selected.company_name}</h2><p className="subtle">Calculated using the upper price band of {selected.price_band}.</p></div><button className="muted" onClick={() => setSelected(null)}>Close</button></div><div className="scenario-grid"><label>GMP used (₹)<input inputMode="decimal" value={gmp} onChange={(event) => setGmp(event.target.value)} placeholder="Example: 20" /></label><div><small>One lot</small><strong>{selected.lot_size ? `${selected.lot_size} shares` : "Lot size unavailable"}</strong></div><div><small>Application amount</small><strong>{lotCost === null ? "Lot size unavailable" : `₹${lotCost.toLocaleString("en-IN")}`}</strong></div><div><small>Listing price at GMP</small><strong>{band && Number.isFinite(gmpNumber) ? `₹${(band + gmpNumber).toFixed(2)}` : "Enter GMP"}</strong></div><div><small>One-lot GMP gain</small><strong>{lotProfit === null ? "Enter GMP and lot size" : `₹${lotProfit.toLocaleString("en-IN")}`}</strong></div><div><small>Gain percentage</small><strong>{scenarioPercent === null ? "Enter GMP" : `${scenarioPercent.toFixed(2)}%`}</strong></div></div><p className="subtle">{selected.gmp_source ?? "Manual GMP"}{selected.gmp_updated_at ? ` · Updated ${selected.gmp_updated_at}` : ""}</p></section>}
    <section className="panel ipo-news"><div className="panel-header"><h2>IPO-related market news</h2><span>{ipoArticles.length} updates</span></div>{ipoArticles.length ? <div className="stack">{ipoArticles.map((article) => <article className="news-item" key={article.article_id}><div className="news-meta"><strong>{article.source}</strong><span>{article.timestamp.slice(0, 10)}</span></div><strong>{article.headline}</strong><p className="subtle">{article.summary}</p>{article.url && <a href={article.url} target="_blank" rel="noreferrer">Read source</a>}</article>)}</div> : <p className="empty-state">No IPO-related headlines are available yet.</p>}</section>
  </main>;
}
