class IsotonicCalibrator:
    """Stub implementation. calibrate() returns probability_raw unchanged until model is trained."""

    def calibrate(self, raw_probability: float, event_type: str) -> float:
        _ = event_type
        return 0.5 + (raw_probability - 0.5) * 0.85
