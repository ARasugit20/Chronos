from datetime import datetime, timezone
from typing import Protocol

from app.models.event import Event
from app.models.theme_mapping import ThemeMapping

HIGH_TRUST_SOURCES = {"sports_mock", "macro_mock", "manual"}


class BaseScorer(Protocol):
    def score(self, event: Event, theme: ThemeMapping) -> float:
        """Returns raw probability 0.0-1.0"""
        ...


class RulesScorer:
    """Default scorer. Uses confidence_prior from ThemeMapping + recency + source weight."""

    CONFIDENCE_THRESHOLD = 0.50

    def score(self, event: Event, theme: ThemeMapping) -> float:
        score = theme.confidence_prior
        now = datetime.now(timezone.utc)
        occurred = event.occurred_at
        if occurred.tzinfo is None:
            occurred = occurred.replace(tzinfo=timezone.utc)
        if (now - occurred).days <= 7:
            score += 0.03
        if event.source in HIGH_TRUST_SOURCES:
            score += 0.02
        return max(0.0, min(1.0, score))


class LightGBMScorer:
    """Stub — loads model from MODEL_PATH env var. Falls back to RulesScorer if model not found."""

    def __init__(self, model_path: str = "") -> None:
        self._fallback = RulesScorer()
        self._model_path = model_path

    def score(self, event: Event, theme: ThemeMapping) -> float:
        if not self._model_path:
            return self._fallback.score(event, theme)
        return self._fallback.score(event, theme)
