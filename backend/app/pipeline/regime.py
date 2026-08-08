# WHY: Classify market regime from event text and configurable macro priors.

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum

from app.config import get_settings
from app.models.event import Event


class Regime(StrEnum):
    RANGE_ROTATION = "RANGE_ROTATION"
    RISK_OFF_GEO = "RISK_OFF_GEO"
    EARNINGS_SELLTHEBEAT = "EARNINGS_SELLTHEBEAT"
    AI_INFRA_STRESS = "AI_INFRA_STRESS"
    NEUTRAL = "NEUTRAL"


@dataclass(frozen=True)
class RegimeSnapshot:
    primary: Regime
    flags: tuple[str, ...] = field(default_factory=tuple)
    risk_multiplier: float = 1.0
    confidence_threshold_boost: float = 0.0
    kelly_fraction_override: float | None = None


_OIL_GEO = re.compile(
    r"oil price|crude oil|opec|energy supply|geopolit|middle east|sanction|war risk|supply shock",
    re.IGNORECASE,
)
_YIELDS = re.compile(
    r"yield|rates rise|fed hold|fomc|interest rate|treasury|inflation data|cpi print",
    re.IGNORECASE,
)
_VIX = re.compile(r"vix|volatility spike|market selloff|risk off", re.IGNORECASE)
_EARNINGS_BEAT = re.compile(
    r"earnings beat|revenue beat|guidance raise|record quarter",
    re.IGNORECASE,
)
_EARNINGS_MISS = re.compile(
    r"earnings miss|revenue miss|guidance cut|sell.?the.?beat|profit warning",
    re.IGNORECASE,
)
_AI_INFRA = re.compile(
    r"ai chip|semiconductor|nvidia|gpu shortage|export control|data center capex",
    re.IGNORECASE,
)
_ROTATION = re.compile(
    r"sector rotation|equal.?weight|breadth|leadership shift|small cap",
    re.IGNORECASE,
)


def _is_august_seasonality(now: datetime | None = None) -> bool:
    settings = get_settings()
    if not settings.august_seasonality_enabled:
        return False
    ts = now or datetime.now(timezone.utc)
    return ts.month == 8


class RegimeTagger:
    """Rule-based regime tagger with configurable macro priors."""

    def tag(self, event: Event, *, now: datetime | None = None) -> RegimeSnapshot:
        settings = get_settings()
        text = f"{event.title} {event.event_type}"
        metadata = event.metadata_json or {}
        flags: list[str] = []

        if _OIL_GEO.search(text) or metadata.get("oil_shock"):
            flags.append("oil_geo_shock")
        if _YIELDS.search(text) or metadata.get("yields_rising"):
            flags.append("rising_yields")
        if _VIX.search(text) or metadata.get("vix_elevated"):
            flags.append("elevated_volatility")
        if _ROTATION.search(text) or settings.default_range_rotation:
            flags.append("range_rotation")
        if _is_august_seasonality(now):
            flags.append("august_seasonality")

        primary = Regime.NEUTRAL
        risk_multiplier = 1.0
        confidence_boost = 0.0
        kelly_override: float | None = None

        if "oil_geo_shock" in flags:
            primary = Regime.RISK_OFF_GEO
            risk_multiplier = settings.regime_risk_off_multiplier
            confidence_boost = settings.regime_confidence_boost_risk_off
            kelly_override = settings.regime_kelly_fraction_risk_off
        elif _AI_INFRA.search(text):
            primary = Regime.AI_INFRA_STRESS
            risk_multiplier = settings.regime_ai_infra_multiplier
            confidence_boost = settings.regime_confidence_boost_ai_infra
            kelly_override = settings.regime_kelly_fraction_ai_infra
        elif _EARNINGS_MISS.search(text) or (
            _EARNINGS_BEAT.search(text) and "sell" in text.lower()
        ):
            primary = Regime.EARNINGS_SELLTHEBEAT
            risk_multiplier = settings.regime_earnings_multiplier
            confidence_boost = settings.regime_confidence_boost_earnings
            kelly_override = settings.regime_kelly_fraction_earnings
        elif "range_rotation" in flags:
            primary = Regime.RANGE_ROTATION
            risk_multiplier = settings.regime_rotation_multiplier

        if "august_seasonality" in flags and primary == Regime.NEUTRAL:
            risk_multiplier = max(risk_multiplier, settings.august_risk_multiplier)

        return RegimeSnapshot(
            primary=primary,
            flags=tuple(flags),
            risk_multiplier=risk_multiplier,
            confidence_threshold_boost=confidence_boost,
            kelly_fraction_override=kelly_override,
        )
