"""add insufficient_evidence to impact_recommendation enum

Revision ID: f3a1c9e7b2d4
Revises: 837e39de40e5
Create Date: 2026-09-02 15:20:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = 'f3a1c9e7b2d4'
down_revision: Union[str, None] = '837e39de40e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE impact_recommendation ADD VALUE IF NOT EXISTS 'INSUFFICIENT_EVIDENCE'")


def downgrade() -> None:
    # Postgres cannot drop a single enum value without recreating the type;
    # not worth the churn for a downgrade path that would never actually run
    # against rows already using it. No-op.
    pass
