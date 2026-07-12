"""remove unit from products

Revision ID: 48789791f9e6
Revises: 9b2c4d7e8f10
Create Date: 2026-07-12 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "48789791f9e6"
down_revision: Union[str, Sequence[str], None] = "9b2c4d7e8f10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_index(op.f("ix_products_unit_id"), table_name="products")
    op.drop_constraint("products_unit_id_fkey", "products", type_="foreignkey")
    op.drop_column("products", "unit_id")


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column("products", sa.Column("unit_id", sa.Uuid(), nullable=True))
    op.create_foreign_key("products_unit_id_fkey", "products", "units", ["unit_id"], ["id"])
    op.create_index(op.f("ix_products_unit_id"), "products", ["unit_id"], unique=False)
