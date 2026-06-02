import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Signal(Base):
    __tablename__ = "signals"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    event_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    ticker: Mapped[str] = mapped_column(String, nullable=False)
    probability_raw: Mapped[float] = mapped_column(nullable=False)
    probability_calibrated: Mapped[float] = mapped_column(nullable=False)
    horizon_hours: Mapped[int] = mapped_column(nullable=False)
    model_version: Mapped[str] = mapped_column(String, nullable=False)
    confidence_bucket: Mapped[str] = mapped_column(String, nullable=False)
    suppressed: Mapped[bool] = mapped_column(default=False, nullable=False)
    suppression_reason: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now(), nullable=False)

    event: Mapped["Event"] = relationship(back_populates="signals")
    recommendation: Mapped[Optional["Recommendation"]] = relationship(back_populates="signal", uselist=False)
