"""add_journal_entries

Revision ID: b187bdae2f0c
Revises: a1b2c3d4e5f6
Create Date: 2026-03-13 08:41:37.167143

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b187bdae2f0c'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('journal_entries',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('garden_id', sa.Integer(), nullable=False),
    sa.Column('planting_id', sa.Integer(), nullable=True),
    sa.Column('entry_date', sa.Date(), nullable=False),
    sa.Column('category', sa.String(length=50), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('tags', sa.JSON(), nullable=True),
    sa.Column('mood', sa.String(length=20), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['garden_id'], ['gardens.id'], ),
    sa.ForeignKeyConstraint(['planting_id'], ['plantings.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('journal_entries')
