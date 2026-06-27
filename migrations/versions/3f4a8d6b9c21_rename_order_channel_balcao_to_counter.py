"""rename order channel balcao to counter

Revision ID: 3f4a8d6b9c21
Revises: c4c542a2213a
Create Date: 2026-06-27 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '3f4a8d6b9c21'
down_revision: Union[str, Sequence[str], None] = 'c4c542a2213a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM pg_enum e
                JOIN pg_type t ON t.oid = e.enumtypid
                WHERE t.typname = 'orderchannel'
                  AND e.enumlabel = 'BALCAO'
            ) THEN
                ALTER TYPE orderchannel RENAME VALUE 'BALCAO' TO 'COUNTER';
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM pg_enum e
                JOIN pg_type t ON t.oid = e.enumtypid
                WHERE t.typname = 'orderchannel'
                  AND e.enumlabel = 'COUNTER'
            ) THEN
                ALTER TYPE orderchannel RENAME VALUE 'COUNTER' TO 'BALCAO';
            END IF;
        END $$;
        """
    )
