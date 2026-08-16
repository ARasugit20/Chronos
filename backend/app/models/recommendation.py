from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import Float, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, NaiveUTCDateTime


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    signal_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("signals.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    action: Mapped[str] = mapped_column(String, nullable=False)
    amount_usd: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    pct_cash: Mapped[float] = mapped_column(nullable=False)
    expires_at: Mapped[datetime] = mapped_column(NaiveUTCDateTime, nullable=False)
    reason: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(default="pending", nullable=False)
    disclaimer: Mapped[str] = mapped_column(default="Research signal only. Not financial advice.", nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=func.now(), nullable=False)
    theme_bucket: Mapped[str | None] = mapped_column(String, nullable=True)
    regime: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    regime_flags: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    calibrated_p: Mapped[float | None] = mapped_column(Float, nullable=True)
    thesis: Mapped[str | None] = mapped_column(String, nullable=True)
    invalidate_if: Mapped[str | None] = mapped_column(String, nullable=True)
    evidence: Mapped[list[Any] | None] = mapped_column(JSONB, nullable=True)
    rank_score: Mapped[float | None] = mapped_column(Float, nullable=True, index=True)
    kelly_half_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    adjustment_reason: Mapped[str | None] = mapped_column(String, nullable=True)

    signal: Mapped[Signal] = relationship(back_populates="recommendation")
    outcome: Mapped[Outcome | None] = relationship(back_populates="recommendation", uselist=False)
