from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Event(Base):
    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    source: Mapped[str] = mapped_column(String, nullable=False)
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    fingerprint_hash: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=func.now(), nullable=False)

    signals: Mapped[list["Signal"]] = relationship(back_populates="event", cascade="all, delete-orphan")
