"""create admin settings

Revision ID: 20260521_0010
Revises: 20260513_0009
Create Date: 2026-05-21 00:10:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260521_0010"
down_revision: Union[str, Sequence[str], None] = "20260513_0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "admin_settings",
        sa.Column("key", sa.String(length=100), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("key"),
    )
    op.execute(
        "INSERT INTO admin_settings (key, value, created_at, updated_at) "
        "VALUES ('image_cors_allowed_origin', '*', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("admin_settings")
