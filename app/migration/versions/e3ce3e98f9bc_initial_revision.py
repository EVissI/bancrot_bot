"""Initial revision

Revision ID: e3ce3e98f9bc
Revises: 
Create Date: 2025-04-13 02:41:53.368348

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e3ce3e98f9bc'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('tel_users',
    sa.Column('telegram_id', sa.BigInteger(), nullable=False),
    sa.Column('username', sa.String(), nullable=True),
    sa.Column('first_name', sa.String(), nullable=False),
    sa.Column('last_name', sa.String(), nullable=True),
    sa.Column('user_enter_first_name', sa.String(), nullable=True),
    sa.Column('user_enter_last_name', sa.String(), nullable=True),
    sa.Column('user_enter_otchestvo', sa.String(), nullable=True),
    sa.Column('data_of_birth', sa.String(), nullable=True),
    sa.Column('region', sa.String(), nullable=True),
    sa.Column('old_last_name', sa.String(), nullable=True),
    sa.Column('end_sub_time', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.PrimaryKeyConstraint('telegram_id'),
    sa.UniqueConstraint('telegram_id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('tel_users')
    # ### end Alembic commands ###
