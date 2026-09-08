from __future__ import annotations

import uuid
from collections import defaultdict

from app.core.clock import utc_now_iso
from app.core.models import NewsArticle, SignalIdea


class SignalService:
    def __init__(self, symbols: list[str]) -> None:
        self.symbols = symbols
        self._latest_signals: list[SignalIdea] = []

    def _market_adjustment(self, tick: dict) -> tuple[float, list[str], list[str]]:
        score = 0.0
        reasons: list[str] = []
        risks: list[str] = []
        if not tick:
            return score, reasons, risks
        if tick["last_price"] > tick["open"]:
            score += 0.7
            reasons.append("trading above session open")
        elif tick["last_price"] < tick["open"]:
            score -= 0.7
            reasons.append("trading below session open")
        if tick["volume"] > 200000:
            score += 0.4
            reasons.append("elevated volume support")
        if tick["volatility"] > 0.025:
            risks.append("high intraday volatility")
            score *= 0.9
        return score, reasons, risks

    def recompute(self, latest_ticks: dict[str, dict], articles: list[NewsArticle], live_prices: dict[str, dict] | None = None) -> list[SignalIdea]:
        articles_by_symbol: dict[str, list[NewsArticle]] = defaultdict(list)
        scores: dict[str, float] = defaultdict(float)
        reasons_map: dict[str, list[str]] = defaultdict(list)
        risks_map: dict[str, list[str]] = defaultdict(list)

        for article in articles:
            for symbol in article.symbols:
                if symbol not in self.symbols:
                    continue
                articles_by_symbol[symbol].append(article)
                scores[symbol] += article.impact_score * 6
                descriptor = article.tags[0] if article.tags else article.sentiment
                reasons_map[symbol].append(f"{article.source}: {descriptor}")
                if article.sentiment == "negative":
                    risks_map[symbol].append("headline sentiment remains negative")

        ideas: list[SignalIdea] = []
        for symbol in self.symbols:
            score = scores[symbol]
            tick = (live_prices or {}).get(symbol) or latest_ticks.get(symbol, {})
            market_score, market_reasons, market_risks = self._market_adjustment(tick)
            score += market_score
            reasons = reasons_map[symbol][:3] + market_reasons[:2]
            risks = list(dict.fromkeys(risks_map[symbol] + market_risks))
            if score >= 6:
                bias = "bullish"
            elif score <= -6:
                bias = "bearish"
            else:
                bias = "neutral"
                if not reasons:
                    reasons = ["insufficient directional confirmation"]
            last_price = tick["last_price"] if tick else None
            change_pct = round(((tick["last_price"] - tick["open"]) / tick["open"]) * 100, 2) if tick and tick["open"] else None
            confidence = min(95.0, max(20.0, 42.0 + abs(score) * 6.5))
            ideas.append(
                SignalIdea(
                    signal_id=f"signal-{uuid.uuid4().hex[:8]}",
                    symbol=symbol,
                    bias=bias,
                    confidence=round(confidence, 1),
                    score=round(score, 2),
                    horizon="today",
                    last_price=last_price,
                    change_pct=change_pct,
                    reasons=list(dict.fromkeys(reasons))[:4],
                    risks=risks[:3],
                    related_articles=[article.article_id for article in articles_by_symbol[symbol][:3]],
                    timestamp=utc_now_iso(),
                )
            )
        ideas.sort(key=lambda idea: (idea.bias == "neutral", -abs(idea.score), -idea.confidence, idea.symbol))
        self._latest_signals = ideas
        return list(self._latest_signals)

    def latest(self) -> list[SignalIdea]:
        return list(self._latest_signals)
