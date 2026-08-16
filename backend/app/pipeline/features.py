# WHY: Extract numeric features from events for ML scoring.

from __future__ import annotations

import hashlib
import json
import re

from app.models.event import Event
from app.models.theme_mapping import ThemeMapping

SOURCE_TRUST: dict[str, float] = {
    "sports_mock": 0.7,
    "macro_mock": 0.9,
    "news_mock": 0.6,
    "finnhub": 0.8,
    "manual": 0.85,
}

DOLLAR_RE = re.compile(r"\$[\d,]+")
FEATURE_NAMES = (
    "hour_of_day",
    "day_of_week",
    "source_trust",
    "title_length",
    "has_dollar_amount",
    "keyword_count",
    "days_to_expiry",
)


def feature_schema_hash() -> str:
    payload = json.dumps(FEATURE_NAMES, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def extract_features(
    event: Event,
    theme: ThemeMapping | None = None,
    *,
    horizon_hours: float = 72.0,
) -> dict[str, float | int | bool]:
    occurred = event.occurred_at
    title = event.title
    pattern = theme.event_pattern if theme else ""
    keyword_hits = sum(1 for part in pattern.split("|") if part and part.lower() in title.lower())
    return {
        "hour_of_day": float(occurred.hour),
        "day_of_week": float(occurred.weekday()),
        "source_trust": SOURCE_TRUST.get(event.source, 0.5),
        "title_length": float(len(title)),
        "has_dollar_amount": bool(DOLLAR_RE.search(title)),
        "keyword_count": float(keyword_hits),
        "days_to_expiry": round(horizon_hours / 24.0, 2),
    }


def features_to_vector(features: dict[str, float | int | bool]) -> list[float]:
    return [
        float(features["hour_of_day"]),
        float(features["day_of_week"]),
        float(features["source_trust"]),
        float(features["title_length"]),
        float(features["has_dollar_amount"]),
        float(features["keyword_count"]),
        float(features["days_to_expiry"]),
    ]
