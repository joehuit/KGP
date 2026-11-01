"""Add tracking_token column to orders table.

Revision ID: 0003_add_order_tracking_token
Revises: 0002_add_idempotency_keys
Create Date: 2026-11-01 11:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0003_add_order_tracking_token"
down_revision: Union[str, None] = "0002_add_idempotency_keys"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("orders", sa.Column("tracking_token", sa.String(length=64), nullable=True))
    op.create_index("ix_orders_tracking_token", "orders", ["tracking_token"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_orders_tracking_token", table_name="orders")
    op.drop_column("orders", "tracking_token")
