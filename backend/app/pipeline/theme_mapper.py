import json
import re
from dataclasses import dataclass
from pathlib import Path

import structlog

from app.models.event import Event
from app.models.theme_mapping import ThemeMapping
from app.pipeline.embedder import cosine_similarity, embed

logger = structlog.get_logger(__name__)
THEME_MAPPINGS_PATH = Path(__file__).resolve().parent.parent / "seeds" / "theme_mappings.json"
REGEX_CONFIDENCE_FLOOR = 0.5


@dataclass(frozen=True)
class ThemeMatch:
    mapping: ThemeMapping
    tickers: list[str]
    match_method: str = "regex"
    confidence: float = 0.0


def load_theme_mappings_from_file() -> list[dict]:
    with THEME_MAPPINGS_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def _regex_confidence(event: Event, mapping: ThemeMapping) -> float:
    if not re.search(mapping.event_pattern, event.title, flags=re.IGNORECASE):
        return 0.0
    return min(1.0, mapping.confidence_prior + 0.05)


def _embedding_confidence(event: Event, mapping: ThemeMapping) -> float:
    text = f"{event.title} {mapping.rationale}"
    return max(0.0, cosine_similarity(embed(event.title), embed(text)))


def match_themes(event: Event, mappings: list[ThemeMapping]) -> list[ThemeMatch]:
    results: list[ThemeMatch] = []
    for mapping in mappings:
        regex_conf = _regex_confidence(event, mapping)
        embed_conf = _embedding_confidence(event, mapping)
        if regex_conf >= REGEX_CONFIDENCE_FLOOR:
            method = "regex"
            confidence = regex_conf
        elif embed_conf > regex_conf and embed_conf >= 0.35:
            method = "embedding"
            confidence = embed_conf
        elif regex_conf > 0:
            method = "regex+embedding"
            confidence = max(regex_conf, embed_conf)
        else:
            continue
        results.append(
            ThemeMatch(
                mapping=mapping,
                tickers=list(mapping.tickers),
                match_method=method,
                confidence=confidence,
            )
        )
        logger.info(
            "theme.matched",
            pattern=mapping.event_pattern,
            method=method,
            confidence=round(confidence, 3),
        )
    return results
