"""Add category to Post

Revision ID: eb4b028bf8ad
Revises: b92525924a98
Create Date: 2026-07-21 22:23:15.322655

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'eb4b028bf8ad'
down_revision: Union[str, Sequence[str], None] = 'b92525924a98'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('post', sa.Column('category', sqlmodel.sql.sqltypes.AutoString(), server_default='Session', nullable=False))



def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('post', 'category')

