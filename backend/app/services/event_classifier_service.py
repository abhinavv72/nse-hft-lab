from __future__ import annotations


class EventClassifierService:
    def __init__(self) -> None:
        self.keyword_tags: dict[str, list[str]] = {
            "wins": ["deal-win", "bullish"],
            "win": ["deal-win", "bullish"],
            "order": ["order-flow"],
            "upbeat": ["guidance-up", "bullish"],
            "strong": ["strong-demand", "bullish"],
            "recovery": ["margin-recovery", "bullish"],
            "growth": ["growth", "bullish"],
            "fundraising": ["capital-raise"],
            "fundraising plan": ["capital-raise"],
            "consider fundraising": ["capital-raise"],
            "resigns": ["management-change", "bearish"],
            "resigns amid": ["management-change", "bearish"],
            "cautious": ["weak-guidance", "bearish"],
            "pressure": ["price-pressure", "bearish"],
            "weak": ["weak-guidance", "bearish"],
            "fragile": ["fragile-sentiment", "bearish"],
            "cut": ["guidance-cut", "bearish"],
            "volatility": ["high-volatility"],
        }

    def classify(self, headline: str, summary: str = "") -> list[str]:
        tags: set[str] = set()
        text = f"{headline} {summary}".lower()
        for phrase, phrase_tags in self.keyword_tags.items():
            if phrase in text:
                tags.update(phrase_tags)
        if not tags:
            tags.add("general-market")
        return sorted(tags)
