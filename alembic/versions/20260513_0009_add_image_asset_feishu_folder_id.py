"""add image asset feishu folder id

Revision ID: 20260513_0009
Revises: 20260513_0008
Create Date: 2026-05-13 01:00:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260513_0009"
down_revision: Union[str, Sequence[str], None] = "20260513_0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("image_host_assets") as batch_op:
        batch_op.add_column(sa.Column("feishu_folder_id", sa.Integer(), nullable=True))
        batch_op.create_index(
            "ix_image_host_assets_feishu_folder_id",
            ["feishu_folder_id"],
            unique=False,
        )
        batch_op.create_foreign_key(
            "fk_image_host_assets_feishu_folder_id",
            "feishu_folders",
            ["feishu_folder_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("image_host_assets") as batch_op:
        batch_op.drop_constraint(
            "fk_image_host_assets_feishu_folder_id",
            type_="foreignkey",
        )
        batch_op.drop_index("ix_image_host_assets_feishu_folder_id")
        batch_op.drop_column("feishu_folder_id")
