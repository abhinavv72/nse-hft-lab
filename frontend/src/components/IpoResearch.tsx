import type { NewsArticle } from "../types";

export default function IpoResearch({ articles }: { articles: NewsArticle[] }) {
  const ipoArticles = articles.filter((article) => /\bipo\b|anchor|listing/i.test(`${article.headline} ${article.summary}`)).slice(0, 8);
  return <main className="product-page">
    <section className="hero-copy"><p className="eyebrow">IPO RESEARCH</p><h2>Research an IPO before applying.</h2><p>Read current coverage and official offer documents. This page does not predict listing returns or recommend an IPO.</p></section>
    <section className="ipo-warning"><strong>GMP is not displayed as a prediction.</strong><span>Grey-market premium is unofficial and unregulated. A number without a verified, timestamped source would be misleading, so this app never invents one.</span></section>
    <section className="ipo-checklist"><h3>Use this checklist for every IPO</h3><div><span>1</span><p>Read the RHP/DRHP and understand the business, debt, risks, and use of proceeds.</p></div><div><span>2</span><p>Compare valuation and fundamentals with listed peers—not only social-media sentiment or GMP.</p></div><div><span>3</span><p>Check price band, lot size, dates, subscription figures, and official exchange notices.</p></div></section>
    <section className="panel ipo-news"><div className="panel-header"><h2>Latest IPO-related news</h2><span>{ipoArticles.length} updates</span></div>{ipoArticles.length ? <div className="stack">{ipoArticles.map((article) => <article className="news-item" key={article.article_id}><div className="news-meta"><strong>{article.source}</strong><span>{article.timestamp.slice(0, 10)}</span></div><strong>{article.headline}</strong><p className="subtle">{article.summary}</p>{article.url && <a href={article.url} target="_blank" rel="noreferrer">Read source</a>}</article>)}</div> : <p className="empty-state">No IPO-related headlines are available yet. Refresh the market research feed.</p>}</section>
  </main>;
}
