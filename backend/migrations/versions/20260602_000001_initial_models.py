"""initial models

Revision ID: 20260602_000001
Revises:
Create Date: 2026-06-02 01:45:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260602_000001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(), nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("fingerprint_hash", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_events")),
    )
    op.create_index(op.f("ix_events_fingerprint_hash"), "events", ["fingerprint_hash"], unique=True)

    op.create_table(
        "theme_mappings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_pattern", sa.String(), nullable=False),
        sa.Column("tickers", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("rationale", sa.String(), nullable=False),
        sa.Column("confidence_prior", sa.Float(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("approved_by_human", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_theme_mappings")),
    )

    op.create_table(
        "signals",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ticker", sa.String(), nullable=False),
        sa.Column("probability_raw", sa.Float(), nullable=False),
        sa.Column("probability_calibrated", sa.Float(), nullable=False),
        sa.Column("horizon_hours", sa.Integer(), nullable=False),
        sa.Column("model_version", sa.String(), nullable=False),
        sa.Column("confidence_bucket", sa.String(), nullable=False),
        sa.Column("suppressed", sa.Boolean(), nullable=False),
        sa.Column("suppression_reason", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], name=op.f("fk_signals_event_id_events"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_signals")),
    )
    op.create_index(op.f("ix_signals_event_id"), "signals", ["event_id"], unique=False)

    op.create_table(
        "recommendations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("signal_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("amount_usd", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("pct_cash", sa.Float(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("reason", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("disclaimer", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["signal_id"], ["signals.id"], name=op.f("fk_recommendations_signal_id_signals"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_recommendations")),
    )
    op.create_index(op.f("ix_recommendations_signal_id"), "recommendations", ["signal_id"], unique=True)

    op.create_table(
        "outcomes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("recommendation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(), nullable=False),
        sa.Column("price_at_signal", sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column("price_at_expiry", sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column("realized_return_pct", sa.Float(), nullable=False),
        sa.Column("hit_boolean", sa.Boolean(), nullable=False),
        sa.Column("brier_component", sa.Float(), nullable=False),
        sa.Column("data_source", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["recommendation_id"],
            ["recommendations.id"],
            name=op.f("fk_outcomes_recommendation_id_recommendations"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_outcomes")),
        sa.UniqueConstraint("recommendation_id", name=op.f("uq_outcomes_recommendation_id")),
    )


def downgrade() -> None:
    op.drop_table("outcomes")
    op.drop_index(op.f("ix_recommendations_signal_id"), table_name="recommendations")
    op.drop_table("recommendations")
    op.drop_index(op.f("ix_signals_event_id"), table_name="signals")
    op.drop_table("signals")
    op.drop_table("theme_mappings")
    op.drop_index(op.f("ix_events_fingerprint_hash"), table_name="events")
    op.drop_table("events")
