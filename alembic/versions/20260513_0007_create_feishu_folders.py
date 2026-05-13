"""create feishu folders

Revision ID: 20260513_0007
Revises: 20260511_0006
Create Date: 2026-05-13 00:00:00

"""

from datetime import datetime, timezone
import os
from pathlib import Path
from typing import Sequence, Union

from alembic import op
from dotenv import dotenv_values
import sqlalchemy as sa


revision: str = "20260513_0007"
down_revision: Union[str, Sequence[str], None] = "20260511_0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ENV_FOLDER_TOKEN_KEY = "IMAGE_HOST_FEISHU_DRIVE_FOLDER_TOKEN"


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "feishu_folders",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("folder_token", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("folder_token"),
    )
    op.create_index(
        "ix_feishu_folders_is_active",
        "feishu_folders",
        ["is_active"],
        unique=False,
    )

    folder_token = _load_existing_folder_token()
    if folder_token:
        now = datetime.now(timezone.utc)
        feishu_folders = sa.table(
            "feishu_folders",
            sa.column("name", sa.String),
            sa.column("folder_token", sa.String),
            sa.column("is_active", sa.Boolean),
            sa.column("created_at", sa.DateTime),
            sa.column("updated_at", sa.DateTime),
        )
        op.bulk_insert(
            feishu_folders,
            [
                {
                    "name": "图床",
                    "folder_token": folder_token,
                    "is_active": True,
                    "created_at": now,
                    "updated_at": now,
                }
            ],
        )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_feishu_folders_is_active", table_name="feishu_folders")
    op.drop_table("feishu_folders")


def _load_existing_folder_token() -> str:
    env_value = os.getenv(ENV_FOLDER_TOKEN_KEY, "").strip()
    if env_value:
        return env_value

    env_path = Path.cwd() / ".env"
    if not env_path.exists():
        return ""
    value = dotenv_values(env_path).get(ENV_FOLDER_TOKEN_KEY)
    return value.strip() if value else ""
