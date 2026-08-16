from datetime import UTC, datetime

import pytest

from app.models.event import Event
from app.pipeline.regime import Regime, RegimeTagger


def _event(title: str, metadata: dict | None = None) -> Event:
    return Event(
        source="news_mock",
        event_type="news",
        title=title,
        occurred_at=datetime(2026, 8, 8, tzinfo=UTC),
        metadata_json=metadata or {},
        fingerprint_hash="regime-test",
    )


def test_oil_geo_regime() -> None:
    tagger = RegimeTagger()
    snapshot = tagger.tag(_event("OPEC cuts crude oil supply amid geopolitical tension"))
    assert snapshot.primary == Regime.RISK_OFF_GEO
    assert "oil_geo_shock" in snapshot.flags
    assert snapshot.kelly_fraction_override is not None


def test_ai_infra_stress_regime() -> None:
    tagger = RegimeTagger()
    snapshot = tagger.tag(_event("NVIDIA AI chip export control hits semiconductor supply"))
    assert snapshot.primary == Regime.AI_INFRA_STRESS


def test_earnings_sellthebeat_regime() -> None:
    tagger = RegimeTagger()
    snapshot = tagger.tag(_event("Company reports earnings beat but sell-the-beat reaction"))
    assert snapshot.primary == Regime.EARNINGS_SELLTHEBEAT


def test_range_rotation_from_config(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.config import get_settings

    settings = get_settings()
    monkeypatch.setattr(settings, "default_range_rotation", True)
    tagger = RegimeTagger()
    snapshot = tagger.tag(_event("Market update on sector leadership"))
    assert snapshot.primary == Regime.RANGE_ROTATION
    assert "range_rotation" in snapshot.flags


def test_august_seasonality_flag() -> None:
    tagger = RegimeTagger()
    snapshot = tagger.tag(_event("Quiet trading day"), now=datetime(2026, 8, 15, tzinfo=UTC))
    assert "august_seasonality" in snapshot.flags
