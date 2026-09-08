import { useEffect, useMemo, useState } from "react";

import { api } from "../api/client";
import type { IpoIssue, NewsArticle } from "../types";

function upperBand(issue: IpoIssue) {
  const values = issue.price_band.match(/\d+(?:\.\d+)?/g)?.map(Number) ?? [];
  return values.length ? Math.max(...values) : null;
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

  return <main className="product-page">
    <section className="hero-copy"><p className="eyebrow">LIVE NSE IPO TRACKER</p><h2>Current IPO dates, price bands and subscription status.</h2><p>Data below is loaded from NSE’s current-issue feed. Use official documents for full issue terms and company risks.</p><button onClick={() => void load()} disabled={loading}>{loading ? "Refreshing official data…" : "Refresh official NSE data"}</button></section>
    <section className="ipo-warning"><strong>About GMP:</strong><span>GMP is unofficial and not provided by NSE. This tracker will not show an invented “live GMP.” The calculator below lets you test a number only as a scenario.</span></section>
    {error && <p className="empty-state">{error}</p>}
    <section className="ipo-grid">
      {issues.map((issue) => <article className="ipo-card" key={`${issue.symbol}-${issue.company_name}`}><div className="watch-card-top"><strong>{issue.company_name}</strong><span className="pill ok">{issue.status}</span></div><span className="subtle">{issue.symbol || "Symbol pending"} · {issue.series || "IPO"}</span><div className="ipo-facts"><div><small>Open</small><b>{issue.open_date || "Not published"}</b></div><div><small>Close</small><b>{issue.close_date || "Not published"}</b></div><div><small>Price band</small><b>{issue.price_band}</b></div><div><small>Subscription</small><b>{issue.subscription_times === null ? "Awaiting data" : `${issue.subscription_times.toFixed(2)}×`}</b></div><div><small>Issue size</small><b>{formatShares(issue.issue_size_shares)} shares</b></div></div><div className="card-actions"><a className="button-link muted" href={issue.official_url} target="_blank" rel="noreferrer">NSE issue page</a><button onClick={() => { setSelected(issue); setGmp(""); }}>Scenario tool</button></div></article>)}
      {!loading && !error && issues.length === 0 && <p className="empty-state">NSE currently reports no active IPO issues.</p>}
    </section>
    {selected && <section className="ipo-scenario"><div className="detail-heading"><div><p className="eyebrow">LISTING-GAIN SCENARIO</p><h2>{selected.company_name}</h2><p className="subtle">Uses the upper price band of {selected.price_band}. This is a calculation, not a forecast.</p></div><button className="muted" onClick={() => setSelected(null)}>Close</button></div><div className="scenario-grid"><label>Unofficial GMP you want to test (₹)<input inputMode="decimal" value={gmp} onChange={(event) => setGmp(event.target.value)} placeholder="Example: 20" /></label><div><small>Upper price band</small><strong>{band ? `₹${band}` : "Not available"}</strong></div><div><small>Scenario listing price</small><strong>{band && Number.isFinite(gmpNumber) ? `₹${(band + gmpNumber).toFixed(2)}` : "Enter GMP"}</strong></div><div><small>Scenario change</small><strong>{scenarioPercent === null ? "Enter GMP" : `${scenarioPercent.toFixed(2)}%`}</strong></div></div><p className="subtle">Do not treat this as expected return. GMP is an unofficial market indication and can change or disappear before listing.</p></section>}
    <section className="panel ipo-news"><div className="panel-header"><h2>IPO-related market news</h2><span>{ipoArticles.length} updates</span></div>{ipoArticles.length ? <div className="stack">{ipoArticles.map((article) => <article className="news-item" key={article.article_id}><div className="news-meta"><strong>{article.source}</strong><span>{article.timestamp.slice(0, 10)}</span></div><strong>{article.headline}</strong><p className="subtle">{article.summary}</p>{article.url && <a href={article.url} target="_blank" rel="noreferrer">Read source</a>}</article>)}</div> : <p className="empty-state">No IPO-related headlines are available yet.</p>}</section>
  </main>;
}
