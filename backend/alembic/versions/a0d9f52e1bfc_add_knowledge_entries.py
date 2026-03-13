"""add_knowledge_entries

Revision ID: a0d9f52e1bfc
Revises: b187bdae2f0c
Create Date: 2026-03-13 08:44:59.166198

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a0d9f52e1bfc'
down_revision: Union[str, None] = 'b187bdae2f0c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('knowledge_entries',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('garden_id', sa.Integer(), nullable=True),
    sa.Column('source_type', sa.String(length=50), nullable=False),
    sa.Column('source_id', sa.Integer(), nullable=True),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('metadata_json', sa.JSON(), nullable=True),
    sa.Column('embedding_vector', sa.Text(), nullable=True),
    sa.Column('chunk_index', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['garden_id'], ['gardens.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('knowledge_entries')
