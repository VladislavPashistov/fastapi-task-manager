"""correction

Revision ID: b24a9ad54671
Revises: 098d3c75d3b4
Create Date: 2026-01-10 00:54:58.732757

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b24a9ad54671'
down_revision: Union[str, Sequence[str], None] = '098d3c75d3b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


color_enum = postgresql.ENUM(
    'blue','red','green','yellow','magenta','cyan','white','black',
    'pink','gray','orange','purple',
    name='color'
)

def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    color_enum.create(bind, checkfirst=True)

    op.alter_column(
        'categories', 'color',
        existing_type=sa.VARCHAR(length=15),
        type_=color_enum,
        postgresql_using="color::color",
        existing_nullable=True,
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        'categories', 'color',
        existing_type=color_enum,
        type_=sa.VARCHAR(length=15),
        postgresql_using="color::text",
        existing_nullable=True,
    )
    # ### end Alembic commands ###
