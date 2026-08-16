from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event
from app.models.outcome import Outcome
from app.models.recommendation import Recommendation
from app.models.signal import Signal
from app.pipeline.quality import SignalQualityGuard


@pytest.mark.asyncio
async def test_low_precision_suppresses(db_session: AsyncSession) -> None:
    event = Event(
        source="manual",
        event_type="sports",
        title="quality test",
        occurred_at=datetime.now(UTC),
        metadata_json={},
        fingerprint_hash="quality-low",
    )
    db_session.add(event)
    await db_session.flush()

    for i in range(12):
        signal = Signal(
            event_id=event.id,
            ticker="BAD",
            probability_raw=0.6,
            probability_calibrated=0.6,
            horizon_hours=72,
            model_version="rules-v1",
            confidence_bucket="medium",
            suppressed=False,
        )
        db_session.add(signal)
        await db_session.flush()
        rec = Recommendation(
            signal_id=signal.id,
            action="buy",
            amount_usd=Decimal(100),
            pct_cash=0.01,
            expires_at=datetime.now(UTC),
            reason="test",
            status="resolved",
        )
        db_session.add(rec)
        await db_session.flush()
        db_session.add(
            Outcome(
                recommendation_id=rec.id,
                resolved_at=datetime.now(UTC),
                price_at_signal=Decimal(100),
                price_at_expiry=Decimal(90),
                realized_return_pct=-0.1,
                hit_boolean=False,
                brier_component=0.4,
                data_source="mock",
            )
        )
    await db_session.commit()

    guard = SignalQualityGuard()
    suppress, reason, _ = await guard.evaluate(db_session, "BAD")
    assert suppress is True
    assert reason == "low_precision_guardrail"
