from __future__ import annotations

import csv
import hashlib
from pathlib import Path
from xml.etree import ElementTree

import httpx

from app.core.clock import utc_now_iso
from app.core.models import NewsArticle
from app.services.event_classifier_service import EventClassifierService
from app.services.ai_sentiment_service import AiSentimentService
from app.services.sentiment_service import SentimentService
from app.services.symbol_mapper_service import SymbolMapperService


class NewsIngestionService:
    def __init__(
        self,
        seed_path: Path,
        mapper: SymbolMapperService,
        classifier: EventClassifierService,
        sentiment: SentimentService,
        feed_urls: list[str],
        max_articles: int,
        live_news_enabled: bool,
        ai_sentiment: AiSentimentService,
    ) -> None:
        self.seed_path = seed_path
        self.mapper = mapper
        self.classifier = classifier
        self.sentiment = sentiment
        self.feed_urls = feed_urls
        self.max_articles = max_articles
        self.live_news_enabled = live_news_enabled
        self.ai_sentiment = ai_sentiment
        self.articles: list[NewsArticle] = []
        self._article_ids: set[str] = set()
        self._seed_loaded = False

    def _make_article_id(self, source: str, headline: str, timestamp: str) -> str:
        base = f"{source}|{headline}|{timestamp}".encode("utf-8")
        return hashlib.sha1(base).hexdigest()[:12]

    async def _build_article(self, timestamp: str, source: str, headline: str, summary: str, url: str) -> NewsArticle:
        tags = self.classifier.classify(headline, summary)
        sentiment_label, impact_score = self.sentiment.score(tags)
        analysis_source = "rules"
        ai_result = await self.ai_sentiment.analyze(headline, summary)
        if ai_result is not None:
            sentiment_label = ai_result.label
            impact_score = ai_result.impact_score
            tags = [f"ai-{ai_result.label}", "finbert", *tags]
            analysis_source = "finbert"
        symbols = self.mapper.map_text(f"{headline} {summary}")
        return NewsArticle(
            article_id=self._make_article_id(source, headline, timestamp),
            timestamp=timestamp,
            source=source,
            headline=headline,
            summary=summary,
            url=url,
            symbols=symbols,
            sentiment=sentiment_label,
            impact_score=impact_score,
            tags=tags,
            analysis_source=analysis_source,
        )

    def _add_article(self, article: NewsArticle) -> bool:
        if article.article_id in self._article_ids:
            return False
        self._article_ids.add(article.article_id)
        self.articles.append(article)
        self.articles.sort(key=lambda item: item.timestamp, reverse=True)
        self.articles = self.articles[: self.max_articles]
        self._article_ids = {item.article_id for item in self.articles}
        return True

    async def load_seed_articles(self) -> list[NewsArticle]:
        if self._seed_loaded:
            return []
        self._seed_loaded = True
        added: list[NewsArticle] = []
        if not self.seed_path.exists():
            return added
        with self.seed_path.open("r", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                article = await self._build_article(
                    row["timestamp"],
                    row["source"],
                    row["headline"],
                    row.get("summary", ""),
                    row.get("url", ""),
                )
                if self._add_article(article):
                    added.append(article)
        return added

    async def _fetch_feed(self, client: httpx.AsyncClient, url: str) -> list[NewsArticle]:
        response = await client.get(url, timeout=10.0, follow_redirects=True)
        response.raise_for_status()
        root = ElementTree.fromstring(response.text)
        added: list[NewsArticle] = []
        for item in root.findall(".//item"):
            headline = (item.findtext("title") or "").strip()
            if not headline:
                continue
            summary = (item.findtext("description") or "").strip()
            article = await self._build_article(
                (item.findtext("pubDate") or utc_now_iso()).strip(),
                root.findtext(".//channel/title") or "RSS",
                headline,
                summary,
                (item.findtext("link") or "").strip(),
            )
            if self._add_article(article):
                added.append(article)
        return added

    async def refresh(self) -> list[NewsArticle]:
        added = await self.load_seed_articles()
        if not self.live_news_enabled:
            return added
        try:
            async with httpx.AsyncClient(headers={"User-Agent": "NSE-HFT-Lab/1.0"}) as client:
                for url in self.feed_urls:
                    added.extend(await self._fetch_feed(client, url))
        except Exception:
            return added
        return added

    def latest(self, limit: int | None = None) -> list[NewsArticle]:
        if limit is None:
            return list(self.articles)
        return list(self.articles[:limit])
