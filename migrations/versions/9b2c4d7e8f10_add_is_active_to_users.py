"""add is_active to users

Revision ID: 9b2c4d7e8f10
Revises: 3f4a8d6b9c21
Create Date: 2026-07-12 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9b2c4d7e8f10"
down_revision: Union[str, Sequence[str], None] = "3f4a8d6b9c21"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "users",
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
    )
    op.alter_column("users", "is_active", server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("users", "is_active")
