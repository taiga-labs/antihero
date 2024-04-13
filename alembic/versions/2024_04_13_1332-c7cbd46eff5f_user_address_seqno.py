"""user address seqno

Revision ID: c7cbd46eff5f
Revises: fcf6cf6ae990
Create Date: 2024-04-13 13:32:58.115690

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c7cbd46eff5f'
down_revision: Union[str, None] = 'fcf6cf6ae990'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('seqno', sa.Integer(), server_default='0', nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'seqno')
    # ### end Alembic commands ###
