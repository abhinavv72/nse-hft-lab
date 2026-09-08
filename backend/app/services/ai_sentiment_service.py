from __future__ import annotations

import logging
from dataclasses import dataclass

import httpx


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AiSentiment:
    label: str
    confidence: float
    impact_score: float


class AiSentimentService:
    """Optional FinBERT inference through Hugging Face's hosted free-tier API.

    The service is intentionally disabled unless a user-owned token is supplied.
    Rules-based scoring remains the safe fallback when inference is unavailable.
    """

    def __init__(self, token: str | None, model: str, timeout_seconds: float) -> None:
        self.token = token.strip() if token else ""
        self.model = model
        self.timeout_seconds = timeout_seconds

    @property
    def enabled(self) -> bool:
        return bool(self.token)

    async def analyze(self, headline: str, summary: str = "") -> AiSentiment | None:
        if not self.enabled:
            return None
        text = f"{headline}. {summary}".strip()
        url = f"https://router.huggingface.co/hf-inference/models/{self.model}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(
                    url,
                    headers={"Authorization": f"Bearer {self.token}"},
                    json={"inputs": text},
                )
                response.raise_for_status()
            predictions = response.json()
            if predictions and isinstance(predictions[0], list):
                predictions = predictions[0]
            if not isinstance(predictions, list) or not predictions:
                return None
            best = max(predictions, key=lambda item: float(item.get("score", 0)))
            label = str(best.get("label", "neutral")).lower()
            if label not in {"positive", "negative", "neutral"}:
                return None
            confidence = round(float(best.get("score", 0)), 3)
            direction = 1 if label == "positive" else -1 if label == "negative" else 0
            return AiSentiment(label, confidence, round(direction * (0.5 + 1.5 * confidence), 2))
        except (httpx.HTTPError, ValueError, TypeError) as exc:
            logger.info("FinBERT inference unavailable; using rules fallback: %s", exc)
            return None
