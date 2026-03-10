"""Make llm_interactions.garden_id nullable for global operations

Revision ID: a1b2c3d4e5f6
Revises: 24c5b35436f6
Create Date: 2026-03-10 12:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | None = "24c5b35436f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("llm_interactions") as batch_op:
        batch_op.alter_column("garden_id", existing_type=sa.Integer(), nullable=True)


def downgrade() -> None:
    with op.batch_alter_table("llm_interactions") as batch_op:
        batch_op.alter_column("garden_id", existing_type=sa.Integer(), nullable=False)
