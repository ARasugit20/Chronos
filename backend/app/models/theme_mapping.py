import uuid
from datetime import datetime

from sqlalchemy import String, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ThemeMapping(Base):
    __tablename__ = "theme_mappings"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    event_pattern: Mapped[str] = mapped_column(String, nullable=False)
    tickers: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
    rationale: Mapped[str] = mapped_column(String, nullable=False)
    confidence_prior: Mapped[float] = mapped_column(nullable=False)
    version: Mapped[int] = mapped_column(default=1, nullable=False)
    approved_by_human: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=func.now(), nullable=False)
