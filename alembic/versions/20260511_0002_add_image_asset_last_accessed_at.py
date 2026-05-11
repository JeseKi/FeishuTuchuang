"""add image asset last accessed at

Revision ID: 20260511_0002
Revises: 20260511_0001
Create Date: 2026-05-11 00:10:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260511_0002"
down_revision: Union[str, Sequence[str], None] = "20260511_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "image_host_assets",
        sa.Column("last_accessed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.execute(
        "UPDATE image_host_assets "
        "SET last_accessed_at = COALESCE(last_accessed_at, created_at)"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("image_host_assets", "last_accessed_at")
