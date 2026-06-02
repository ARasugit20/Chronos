import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Outcome(Base):
    __tablename__ = "outcomes"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    recommendation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("recommendations.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    resolved_at: Mapped[datetime] = mapped_column(nullable=False)
    price_at_signal: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    price_at_expiry: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    realized_return_pct: Mapped[float] = mapped_column(nullable=False)
    hit_boolean: Mapped[bool] = mapped_column(nullable=False)
    brier_component: Mapped[float] = mapped_column(nullable=False)
    data_source: Mapped[str] = mapped_column(String, nullable=False)

    recommendation: Mapped["Recommendation"] = relationship(back_populates="outcome")
