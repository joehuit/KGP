"""Add idempotency keys table for duplicate submission prevention.

Revision ID: 0002_add_idempotency_keys
Revises: 0001_initial_schema
Create Date: 2026-11-01 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0002_add_idempotency_keys"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "idempotency_keys",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("key", sa.String(length=128), nullable=False),
        sa.Column("request_hash", sa.String(length=64), nullable=False, comment="SHA-256 hash of (path + customer identity + payload)"),
        sa.Column("response_code", sa.Integer(), nullable=False),
        sa.Column("response_body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_idempotency_keys_id", "idempotency_keys", ["id"])
    op.create_index("ix_idempotency_keys_key", "idempotency_keys", ["key"], unique=True)
    op.create_index("ix_idempotency_keys_request_hash", "idempotency_keys", ["request_hash"])
    op.create_index("ix_idempotency_keys_created_at", "idempotency_keys", ["created_at"])
    op.create_index("ix_idempotency_keys_expires_at", "idempotency_keys", ["expires_at"])


def downgrade() -> None:
    op.drop_index("ix_idempotency_keys_expires_at", table_name="idempotency_keys")
    op.drop_index("ix_idempotency_keys_created_at", table_name="idempotency_keys")
    op.drop_index("ix_idempotency_keys_request_hash", table_name="idempotency_keys")
    op.drop_index("ix_idempotency_keys_key", table_name="idempotency_keys")
    op.drop_index("ix_idempotency_keys_id", table_name="idempotency_keys")
    op.drop_table("idempotency_keys")
