"""add product categories

Revision ID: 6f2a1b9c8d30
Revises: 48789791f9e6
Create Date: 2026-07-12 00:00:00.000000

"""

import uuid
from datetime import datetime, timezone
from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "6f2a1b9c8d30"
down_revision: Union[str, Sequence[str], None] = "48789791f9e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "product_categories",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("updated_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "uq_product_categories_name_lower",
        "product_categories",
        [sa.text("lower(name)")],
        unique=True,
    )
    connection = op.get_bind()
    categories = connection.execute(
        sa.text(
            """
            SELECT DISTINCT ON (lower(btrim(category))) btrim(category) AS category
            FROM products
            WHERE category IS NOT NULL AND btrim(category) <> ''
            ORDER BY lower(btrim(category)), btrim(category)
            """
        )
    ).fetchall()
    if categories:
        now = datetime.now(timezone.utc)
        op.bulk_insert(
            sa.table(
                "product_categories",
                sa.column("id", sa.Uuid()),
                sa.column("name", sa.String()),
                sa.column("created_at", postgresql.TIMESTAMP(timezone=True)),
                sa.column("updated_at", postgresql.TIMESTAMP(timezone=True)),
            ),
            [
                {
                    "id": uuid.uuid4(),
                    "name": category.category,
                    "created_at": now,
                    "updated_at": now,
                }
                for category in categories
            ],
        )
    op.add_column("products", sa.Column("category_id", sa.Uuid(), nullable=True))
    op.execute(
        """
        UPDATE products
        SET category_id = product_categories.id
        FROM product_categories
        WHERE lower(product_categories.name) = lower(products.category)
        """
    )
    op.alter_column("products", "category_id", nullable=False)
    op.create_foreign_key(
        "products_category_id_fkey",
        "products",
        "product_categories",
        ["category_id"],
        ["id"],
    )
    op.create_index(op.f("ix_products_category_id"), "products", ["category_id"], unique=False)
    op.drop_index(op.f("ix_products_category"), table_name="products")
    op.drop_column("products", "category")


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column(
        "products",
        sa.Column("category", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=True),
    )
    op.execute(
        """
        UPDATE products
        SET category = product_categories.name
        FROM product_categories
        WHERE products.category_id = product_categories.id
        """
    )
    op.alter_column("products", "category", nullable=False)
    op.create_index(op.f("ix_products_category"), "products", ["category"], unique=False)
    op.drop_index(op.f("ix_products_category_id"), table_name="products")
    op.drop_constraint("products_category_id_fkey", "products", type_="foreignkey")
    op.drop_column("products", "category_id")
    op.drop_index("uq_product_categories_name_lower", table_name="product_categories")
    op.drop_table("product_categories")
