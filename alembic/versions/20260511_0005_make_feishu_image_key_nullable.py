"""make feishu image key nullable

Revision ID: 20260511_0005
Revises: 20260511_0004
Create Date: 2026-05-11 17:25:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260511_0005"
down_revision: Union[str, Sequence[str], None] = "20260511_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("image_host_assets") as batch_op:
        batch_op.alter_column(
            "feishu_image_key",
            existing_type=sa.String(length=255),
            nullable=True,
        )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        "UPDATE image_host_assets SET feishu_image_key = '' "
        "WHERE feishu_image_key IS NULL"
    )
    with op.batch_alter_table("image_host_assets") as batch_op:
        batch_op.alter_column(
            "feishu_image_key",
            existing_type=sa.String(length=255),
            nullable=False,
        )
