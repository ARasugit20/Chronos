import pytest

from app.pipeline.lead_ranker import (
    LeadCandidate,
    apply_regime_policy,
    build_invalidate_if,
    compute_expected_value,
    compute_rank_score,
    evaluate_lead,
)
from app.pipeline.regime import Regime, RegimeSnapshot
from app.pipeline.theme_buckets import resolve_theme_bucket
from app.models.theme_mapping import ThemeMapping


def _candidate(**overrides) -> LeadCandidate:
    regime = RegimeSnapshot(primary=Regime.NEUTRAL, flags=())
    base = LeadCandidate(
        ticker="XOM",
        calibrated_p=0.65,
        expected_value=5.0,
        risk=10.0,
        rank_score=0.5,
        theme_bucket="ENERGY_SHOCK",
        regime=regime,
        thesis="test thesis",
        invalidate_if="test invalidate",
    )
    for key, value in overrides.items():
        setattr(base, key, value)
    return base


def test_compute_rank_score() -> None:
    regime = RegimeSnapshot(primary=Regime.RISK_OFF_GEO, flags=("oil_geo_shock",), risk_multiplier=1.5)
    score = compute_rank_score(expected_value=10.0, risk=5.0, regime=regime)
    assert score == pytest.approx(10.0 / (5.0 * 1.5))


def test_evaluate_lead_rejects_low_confidence() -> None:
    decision = evaluate_lead(_candidate(calibrated_p=0.40))
    assert decision.promote is False
    assert decision.action == "skip"


def test_evaluate_lead_promotes_strong_candidate() -> None:
    decision = evaluate_lead(_candidate())
    assert decision.promote is True
    assert decision.action == "paper_buy"


def test_apply_regime_policy_boosts_energy_shock() -> None:
    regime = RegimeSnapshot(primary=Regime.RISK_OFF_GEO, flags=("oil_geo_shock",))
    candidate = apply_regime_policy(_candidate(regime=regime, rank_score=1.0))
    assert candidate.rank_score > 1.0


def test_build_invalidate_if_includes_regime() -> None:
    regime = RegimeSnapshot(primary=Regime.EARNINGS_SELLTHEBEAT, flags=())
    text = build_invalidate_if("AI_INFRA", regime, "NVDA")
    assert "NVDA" in text
    assert "24h" in text


def test_theme_bucket_prefers_ai_adopter() -> None:
    mapping = ThemeMapping(
        event_pattern="enterprise ai adoption and ai chip demand",
        tickers=["MSFT"],
        rationale="enterprise ai adoption with semiconductor demand",
        confidence_prior=0.6,
        approved_by_human=True,
    )
    bucket = resolve_theme_bucket(mapping)
    assert bucket == "AI_ADOPTER"


def test_compute_expected_value() -> None:
    ev = compute_expected_value(0.6, 0.02, 1000.0)
    assert ev == pytest.approx(12.0)
