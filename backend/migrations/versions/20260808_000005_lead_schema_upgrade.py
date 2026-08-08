"""add lead schema fields to recommendations

Revision ID: 20260808_000005
Revises: 20260714_000004
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260808_000005"
down_revision: str | None = "20260714_000004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("recommendations", sa.Column("theme_bucket", sa.String(), nullable=True))
    op.add_column("recommendations", sa.Column("regime", sa.String(), nullable=True))
    op.add_column(
        "recommendations",
        sa.Column("regime_flags", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column("recommendations", sa.Column("calibrated_p", sa.Float(), nullable=True))
    op.add_column("recommendations", sa.Column("thesis", sa.String(), nullable=True))
    op.add_column("recommendations", sa.Column("invalidate_if", sa.String(), nullable=True))
    op.add_column(
        "recommendations",
        sa.Column("evidence", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column("recommendations", sa.Column("rank_score", sa.Float(), nullable=True))
    op.add_column("recommendations", sa.Column("kelly_half_pct", sa.Float(), nullable=True))
    op.add_column("recommendations", sa.Column("adjustment_reason", sa.String(), nullable=True))
    op.create_index(
        op.f("ix_recommendations_rank_score"),
        "recommendations",
        ["rank_score"],
    )
    op.create_index(
        op.f("ix_recommendations_regime"),
        "recommendations",
        ["regime"],
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_recommendations_regime"), table_name="recommendations")
    op.drop_index(op.f("ix_recommendations_rank_score"), table_name="recommendations")
    op.drop_column("recommendations", "adjustment_reason")
    op.drop_column("recommendations", "kelly_half_pct")
    op.drop_column("recommendations", "rank_score")
    op.drop_column("recommendations", "evidence")
    op.drop_column("recommendations", "invalidate_if")
    op.drop_column("recommendations", "thesis")
    op.drop_column("recommendations", "calibrated_p")
    op.drop_column("recommendations", "regime_flags")
    op.drop_column("recommendations", "regime")
    op.drop_column("recommendations", "theme_bucket")
