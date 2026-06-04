"""add match_method to signal

Revision ID: 20260602_000003
Revises: 20260602_000002
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260602_000003"
down_revision: str | None = "20260602_000002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("signals", sa.Column("match_method", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("signals", "match_method")
