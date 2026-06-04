# WHY: Calibrate raw model probabilities using fitted isotonic regression.

from __future__ import annotations

from pathlib import Path

import structlog

logger = structlog.get_logger(__name__)
DEFAULT_CALIB_PATH = Path("models/isotonic_calibrator.pkl")


class IsotonicCalibrator:
    def __init__(self, model_path: Path | None = None) -> None:
        self._path = model_path or DEFAULT_CALIB_PATH
        self._model = None
        if self._path.exists():
            try:
                import joblib

                self._model = joblib.load(self._path)
            except Exception as exc:  # noqa: BLE001
                logger.warning("calibrator.load_failed", error=str(exc))

    def fit(self, raw_probs: list[float], outcomes: list[int]) -> None:
        if len(raw_probs) < 5:
            return
        import joblib
        from sklearn.isotonic import IsotonicRegression

        model = IsotonicRegression(out_of_bounds="clip")
        model.fit(raw_probs, outcomes)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(model, self._path)
        self._model = model

    def calibrate(self, raw_probability: float, event_type: str = "") -> float:
        _ = event_type
        if self._model is not None:
            try:
                return float(self._model.predict([raw_probability])[0])
            except Exception as exc:  # noqa: BLE001
                logger.warning("calibrator.predict_failed", error=str(exc))
        logger.debug("calibrator.fallback_shrinkage")
        return 0.85 * raw_probability + 0.075

    @staticmethod
    def evaluate(raw_probs: list[float], outcomes: list[int]) -> dict[str, float]:
        import numpy as np

        raw_arr = np.array(raw_probs)
        out_arr = np.array(outcomes)
        brier_raw = float(np.mean((raw_arr - out_arr) ** 2))
        cal = IsotonicCalibrator()
        cal.fit(raw_probs, outcomes)
        calibrated = [cal.calibrate(p) for p in raw_probs]
        brier_cal = float(np.mean((np.array(calibrated) - out_arr) ** 2))
        return {"brier_raw": brier_raw, "brier_calibrated": brier_cal}
