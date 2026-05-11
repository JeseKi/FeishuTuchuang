"""add drive file token

Revision ID: 20260511_0003
Revises: 20260511_0002
Create Date: 2026-05-11 00:20:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260511_0003"
down_revision: Union[str, Sequence[str], None] = "20260511_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "image_host_assets",
        sa.Column("feishu_file_token", sa.String(length=255), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("image_host_assets", "feishu_file_token")
