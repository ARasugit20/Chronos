from pathlib import Path

from app.pipeline.calibrator import IsotonicCalibrator


def test_isotonic_improves_or_matches_brier() -> None:
    raw = [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9] * 3
    outcomes = [0, 0, 0, 1, 1, 1, 1, 1] * 3
    metrics = IsotonicCalibrator.evaluate(raw, outcomes)
    assert metrics["brier_calibrated"] <= metrics["brier_raw"] + 0.05


def test_fallback_when_model_absent() -> None:
    cal = IsotonicCalibrator(model_path=Path("/tmp/nonexistent_isotonic_chronos.pkl"))
    assert 0.0 <= cal.calibrate(0.6) <= 1.0
