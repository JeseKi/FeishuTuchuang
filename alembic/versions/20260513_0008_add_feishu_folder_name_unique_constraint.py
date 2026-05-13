"""add feishu folder name unique constraint

Revision ID: 20260513_0008
Revises: 20260513_0007
Create Date: 2026-05-13 00:30:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260513_0008"
down_revision: Union[str, Sequence[str], None] = "20260513_0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

CONSTRAINT_NAME = "uq_feishu_folders_name"
MAX_FOLDER_NAME_LENGTH = 100


def upgrade() -> None:
    """Upgrade schema."""
    _deduplicate_existing_names()
    with op.batch_alter_table("feishu_folders") as batch_op:
        batch_op.create_unique_constraint(CONSTRAINT_NAME, ["name"])


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("feishu_folders") as batch_op:
        batch_op.drop_constraint(CONSTRAINT_NAME, type_="unique")


def _deduplicate_existing_names() -> None:
    connection = op.get_bind()
    rows = connection.execute(
        sa.text(
            """
            SELECT id, name
            FROM feishu_folders
            ORDER BY name ASC, id ASC
            """
        )
    ).mappings()

    seen_names: set[str] = set()
    for row in rows:
        folder_id = int(row["id"])
        name = str(row["name"])
        if name not in seen_names:
            seen_names.add(name)
            continue

        new_name = _build_unique_name(name, folder_id, seen_names)
        connection.execute(
            sa.text("UPDATE feishu_folders SET name = :name WHERE id = :id"),
            {"name": new_name, "id": folder_id},
        )
        seen_names.add(new_name)


def _build_unique_name(name: str, folder_id: int, seen_names: set[str]) -> str:
    suffix = f"-{folder_id}"
    base = name[: MAX_FOLDER_NAME_LENGTH - len(suffix)]
    candidate = f"{base}{suffix}"
    if candidate not in seen_names:
        return candidate

    counter = 2
    while True:
        suffix = f"-{folder_id}-{counter}"
        base = name[: MAX_FOLDER_NAME_LENGTH - len(suffix)]
        candidate = f"{base}{suffix}"
        if candidate not in seen_names:
            return candidate
        counter += 1
