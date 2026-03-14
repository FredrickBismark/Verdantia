"""add_alerts

Revision ID: 36c78d38d2a1
Revises: a0d9f52e1bfc
Create Date: 2026-03-13 09:00:07.369037

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '36c78d38d2a1'
down_revision: Union[str, None] = 'a0d9f52e1bfc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('alerts',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('garden_id', sa.Integer(), nullable=False),
    sa.Column('planting_id', sa.Integer(), nullable=True),
    sa.Column('alert_type', sa.String(length=50), nullable=False),
    sa.Column('severity', sa.String(length=20), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('source', sa.String(length=50), nullable=False),
    sa.Column('trigger_date', sa.Date(), nullable=False),
    sa.Column('triggered_at', sa.DateTime(), nullable=False),
    sa.Column('acknowledged', sa.Boolean(), nullable=False),
    sa.Column('acknowledged_at', sa.DateTime(), nullable=True),
    sa.Column('dismissed', sa.Boolean(), nullable=False),
    sa.Column('dismissed_at', sa.DateTime(), nullable=True),
    sa.Column('metadata_json', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['garden_id'], ['gardens.id'], ),
    sa.ForeignKeyConstraint(['planting_id'], ['plantings.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('alerts')
