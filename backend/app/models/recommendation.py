from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


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
    expires_at: Mapped[datetime] = mapped_column(nullable=False)
    reason: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(default="pending", nullable=False)
    disclaimer: Mapped[str] = mapped_column(default="Research signal only. Not financial advice.", nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=func.now(), nullable=False)

    signal: Mapped["Signal"] = relationship(back_populates="recommendation")
    outcome: Mapped[Optional["Outcome"]] = relationship(back_populates="recommendation", uselist=False)
