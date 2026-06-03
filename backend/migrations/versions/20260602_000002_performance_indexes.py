"""performance indexes

Revision ID: 20260602_000002
Revises: 20260602_000001
Create Date: 2026-06-02 12:00:00
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260602_000002"
down_revision: str | None = "20260602_000001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index("ix_signals_created_at", "signals", ["created_at"], unique=False)
    op.create_index("ix_signals_suppressed_created_at", "signals", ["suppressed", "created_at"], unique=False)
    op.create_index("ix_recommendations_status_created_at", "recommendations", ["status", "created_at"], unique=False)
    op.create_index("ix_recommendations_expires_at", "recommendations", ["expires_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_recommendations_expires_at", table_name="recommendations")
    op.drop_index("ix_recommendations_status_created_at", table_name="recommendations")
    op.drop_index("ix_signals_suppressed_created_at", table_name="signals")
    op.drop_index("ix_signals_created_at", table_name="signals")
