from __future__ import annotations


class SentimentService:
    def __init__(self) -> None:
        self.tag_weights: dict[str, float] = {
            "bullish": 1.1,
            "deal-win": 1.4,
            "guidance-up": 1.6,
            "strong-demand": 1.3,
            "margin-recovery": 1.2,
            "growth": 0.8,
            "capital-raise": 0.4,
            "bearish": -1.1,
            "management-change": -1.3,
            "weak-guidance": -1.5,
            "price-pressure": -1.1,
            "fragile-sentiment": -0.8,
            "guidance-cut": -1.6,
            "high-volatility": -0.3,
        }

    def score(self, tags: list[str]) -> tuple[str, float]:
        score = sum(self.tag_weights.get(tag, 0.0) for tag in tags)
        if score > 0.4:
            return "positive", round(score, 2)
        if score < -0.4:
            return "negative", round(score, 2)
        return "neutral", round(score, 2)
