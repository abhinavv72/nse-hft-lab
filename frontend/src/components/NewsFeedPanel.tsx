import type { NewsArticle } from "../types";

interface NewsFeedPanelProps {
  articles: NewsArticle[];
}

export default function NewsFeedPanel({ articles }: NewsFeedPanelProps) {
  return (
    <div>
      <div className="panel-header">
        <h2>News Feed</h2>
        <span>{articles.length} headlines</span>
      </div>
      <div className="stack">
        {articles.length === 0 && <p className="empty-state">News will appear here after the market service connects.</p>}
        {articles.slice(0, 8).map((article) => (
          <div className="news-item" key={article.article_id}>
            <div className="news-meta">
              <strong>{article.source}</strong>
              <span>{article.sentiment}</span>
              <span>{article.analysis_source === "finbert" ? "AI analyzed" : "rules fallback"}</span>
              <span>{article.symbols.join(", ") || "macro"}</span>
            </div>
            <div className="stack tight">
              <span>{article.headline}</span>
              {article.summary ? <span className="subtle">{article.summary}</span> : null}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
