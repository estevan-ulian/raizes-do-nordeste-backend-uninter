"""allow anonymous orders

Revision ID: a7d4c2e9b1f0
Revises: 6f2a1b9c8d30
Create Date: 2026-07-12 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a7d4c2e9b1f0"
down_revision: Union[str, Sequence[str], None] = "6f2a1b9c8d30"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column("orders", "customer_id", existing_type=sa.Uuid(), nullable=True)
    op.add_column(
        "orders",
        sa.Column(
            "payment_method",
            sqlmodel.sql.sqltypes.AutoString(length=50),
            server_default="MOCK",
            nullable=False,
        ),
    )
    op.alter_column("orders", "payment_method", server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("orders", "payment_method")
    op.alter_column("orders", "customer_id", existing_type=sa.Uuid(), nullable=False)
