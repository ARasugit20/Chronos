from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Float, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base, NaiveUTCDateTime


class ModelRun(Base):
    __tablename__ = "model_runs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    model_version: Mapped[str] = mapped_column(String, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="candidate")
    dataset_start_at: Mapped[datetime | None] = mapped_column(NaiveUTCDateTime, nullable=True)
    dataset_cutoff_at: Mapped[datetime | None] = mapped_column(NaiveUTCDateTime, nullable=True)
    feature_schema_hash: Mapped[str] = mapped_column(String, nullable=False)
    artifact_path: Mapped[str] = mapped_column(String, nullable=False)
    train_samples: Mapped[int] = mapped_column(Integer, nullable=False)
    calibrate_samples: Mapped[int] = mapped_column(Integer, nullable=False)
    test_samples: Mapped[int] = mapped_column(Integer, nullable=False)
    train_brier: Mapped[float | None] = mapped_column(Float, nullable=True)
    oos_brier: Mapped[float | None] = mapped_column(Float, nullable=True)
    oos_hit_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    parameters_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=func.now(), nullable=False)
