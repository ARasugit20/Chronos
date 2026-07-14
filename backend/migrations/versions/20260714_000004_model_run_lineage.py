"""add model run lineage

Revision ID: 20260714_000004
Revises: 20260602_000003
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260714_000004"
down_revision: str | None = "20260602_000003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "model_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("model_version", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("dataset_start_at", sa.DateTime(), nullable=True),
        sa.Column("dataset_cutoff_at", sa.DateTime(), nullable=True),
        sa.Column("feature_schema_hash", sa.String(), nullable=False),
        sa.Column("artifact_path", sa.String(), nullable=False),
        sa.Column("train_samples", sa.Integer(), nullable=False),
        sa.Column("calibrate_samples", sa.Integer(), nullable=False),
        sa.Column("test_samples", sa.Integer(), nullable=False),
        sa.Column("train_brier", sa.Float(), nullable=True),
        sa.Column("oos_brier", sa.Float(), nullable=True),
        sa.Column("oos_hit_rate", sa.Float(), nullable=True),
        sa.Column("parameters_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_model_runs")),
    )
    op.create_index(op.f("ix_model_runs_model_version"), "model_runs", ["model_version"])


def downgrade() -> None:
    op.drop_index(op.f("ix_model_runs_model_version"), table_name="model_runs")
    op.drop_table("model_runs")
