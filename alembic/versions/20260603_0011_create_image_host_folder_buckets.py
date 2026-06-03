"""create image host folder buckets

Revision ID: 20260603_0011
Revises: 20260521_0010
Create Date: 2026-06-03 00:00:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260603_0011"
down_revision: Union[str, Sequence[str], None] = "20260521_0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "image_host_feishu_folder_buckets",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("feishu_folder_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("folder_token", sa.String(length=255), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("assigned_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["feishu_folder_id"],
            ["feishu_folders.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("folder_token"),
        sa.UniqueConstraint(
            "feishu_folder_id",
            "sequence",
            name="uq_image_host_feishu_folder_buckets_folder_sequence",
        ),
    )
    op.create_index(
        "ix_image_host_feishu_folder_buckets_feishu_folder_id",
        "image_host_feishu_folder_buckets",
        ["feishu_folder_id"],
        unique=False,
    )

    with op.batch_alter_table("image_host_assets") as batch_op:
        batch_op.add_column(
            sa.Column("feishu_folder_bucket_id", sa.Integer(), nullable=True)
        )
        batch_op.create_index(
            "ix_image_host_assets_feishu_folder_bucket_id",
            ["feishu_folder_bucket_id"],
            unique=False,
        )
        batch_op.create_foreign_key(
            "fk_image_host_assets_feishu_folder_bucket_id",
            "image_host_feishu_folder_buckets",
            ["feishu_folder_bucket_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("image_host_assets") as batch_op:
        batch_op.drop_constraint(
            "fk_image_host_assets_feishu_folder_bucket_id",
            type_="foreignkey",
        )
        batch_op.drop_index("ix_image_host_assets_feishu_folder_bucket_id")
        batch_op.drop_column("feishu_folder_bucket_id")

    op.drop_index(
        "ix_image_host_feishu_folder_buckets_feishu_folder_id",
        table_name="image_host_feishu_folder_buckets",
    )
    op.drop_table("image_host_feishu_folder_buckets")
