import json
import re
from dataclasses import dataclass
from pathlib import Path

from app.models.event import Event
from app.models.theme_mapping import ThemeMapping

THEME_MAPPINGS_PATH = Path(__file__).resolve().parent.parent / "seeds" / "theme_mappings.json"


@dataclass(frozen=True)
class ThemeMatch:
    mapping: ThemeMapping
    tickers: list[str]


def load_theme_mappings_from_file() -> list[dict]:
    with THEME_MAPPINGS_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def match_themes(event: Event, mappings: list[ThemeMapping]) -> list[ThemeMatch]:
    title = event.title.lower()
    matches: list[ThemeMatch] = []
    for mapping in mappings:
        if re.search(mapping.event_pattern, title, flags=re.IGNORECASE):
            matches.append(ThemeMatch(mapping=mapping, tickers=list(mapping.tickers)))
    return matches
