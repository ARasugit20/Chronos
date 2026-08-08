# WHY: Map theme patterns to investable theme buckets for ranking and analytics.

from __future__ import annotations

import re

from app.models.theme_mapping import ThemeMapping

THEME_BUCKETS = {
    "ENERGY_SHOCK": re.compile(
        r"oil price|crude oil|opec|energy supply|xle|natural gas",
        re.IGNORECASE,
    ),
    "FINANCIALS_STRENGTH": re.compile(
        r"federal reserve|fed rate|fomc|bank earnings|financial strength|yield curve",
        re.IGNORECASE,
    ),
    "AI_ADOPTER": re.compile(
        r"enterprise ai|ai adoption|software ai|cloud ai|copilot|automation",
        re.IGNORECASE,
    ),
    "QUALITY_DEFENSIVE": re.compile(
        r"defensive|staples|healthcare|utilities|quality factor",
        re.IGNORECASE,
    ),
    "CONSUMER_WEAKNESS": re.compile(
        r"retail sales miss|consumer confidence|spending slowdown|discretionary weakness",
        re.IGNORECASE,
    ),
    "AI_INFRA": re.compile(
        r"ai chip|semiconductor|nvidia|gpu|data center|export control|smci",
        re.IGNORECASE,
    ),
}

FAVORABLE_BUCKETS = frozenset({"ENERGY_SHOCK", "FINANCIALS_STRENGTH", "AI_ADOPTER", "QUALITY_DEFENSIVE"})
CAUTION_BUCKETS = frozenset({"CONSUMER_WEAKNESS", "AI_INFRA"})


def resolve_theme_bucket(mapping: ThemeMapping, event_title: str = "") -> str:
    text = f"{mapping.event_pattern} {mapping.rationale} {event_title}"
    matches: list[str] = []
    for bucket, pattern in THEME_BUCKETS.items():
        if pattern.search(text):
            matches.append(bucket)

    if "AI_ADOPTER" in matches and "AI_INFRA" in matches:
        matches = [b for b in matches if b != "AI_INFRA"]
    if not matches:
        return "GENERAL"
    if "AI_ADOPTER" in matches:
        return "AI_ADOPTER"
    return matches[0]
