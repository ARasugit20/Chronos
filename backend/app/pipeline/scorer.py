from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol

import structlog

from app.models.event import Event
from app.models.theme_mapping import ThemeMapping
from app.pipeline.features import extract_features, features_to_vector

logger = structlog.get_logger(__name__)
HIGH_TRUST_SOURCES = {"sports_mock", "macro_mock", "manual", "finnhub"}
DEFAULT_MODEL_PATH = Path("models/lgbm_scorer.pkl")


class BaseScorer(Protocol):
    def score(self, event: Event, theme: ThemeMapping) -> float:
        """Returns raw probability 0.0-1.0"""
        ...


class RulesScorer:
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
    def __init__(self, model_path: str = "") -> None:
        self._fallback = RulesScorer()
        self._model_path = Path(model_path) if model_path else DEFAULT_MODEL_PATH
        self._model = None
        if self._model_path.exists():
            try:
                import joblib

                self._model = joblib.load(self._model_path)
            except Exception as exc:  # noqa: BLE001
                logger.warning("scorer.model_load_failed", path=str(self._model_path), error=str(exc))

    def score(self, event: Event, theme: ThemeMapping) -> float:
        if self._model is None:
            return self._fallback.score(event, theme)
        features = extract_features(event, theme)
        vector = [features_to_vector(features)]
        try:
            proba = self._model.predict_proba(vector)[0][1]
            return max(0.0, min(1.0, float(proba)))
        except Exception as exc:  # noqa: BLE001
            logger.warning("scorer.predict_failed", error=str(exc))
            return self._fallback.score(event, theme)

    @classmethod
    def train(cls, X: list[list[float]], y: list[int], model_path: Path | None = None) -> float:
        import joblib
        import lightgbm as lgb
        import numpy as np

        path = model_path or DEFAULT_MODEL_PATH
        path.parent.mkdir(parents=True, exist_ok=True)
        model = lgb.LGBMClassifier(
            n_estimators=100,
            learning_rate=0.05,
            num_leaves=31,
            verbose=-1,
        )
        model.fit(np.array(X), np.array(y))
        joblib.dump(model, path)
        preds = model.predict_proba(np.array(X))[:, 1]
        brier = float(np.mean((preds - np.array(y)) ** 2))
        logger.info("scorer.trained", path=str(path), brier=brier)
        return brier
