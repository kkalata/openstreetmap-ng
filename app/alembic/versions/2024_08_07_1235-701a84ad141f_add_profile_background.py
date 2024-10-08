"""Add profile background

Revision ID: 701a84ad141f
Revises: 194c0c86a069
Create Date: 2024-08-07 12:35:47.982636+00:00

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '701a84ad141f'
down_revision: str | None = '194c0c86a069'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('background_id', sa.Unicode(length=64), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user', 'background_id')
    # ### end Alembic commands ###
