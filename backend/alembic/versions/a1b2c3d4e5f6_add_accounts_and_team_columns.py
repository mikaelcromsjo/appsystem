"""add accounts table and team columns to callers

Revision ID: a1b2c3d4e5f6
Revises: 764db1abccba
Create Date: 2026-04-08

Changes:
- Create accounts table (id, name, extra)
- Add account_id FK column to callers table
- Add extra JSON column to callers table
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "764db1abccba"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # accounts table may already exist if SQLAlchemy create_all() ran first
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "accounts" not in inspector.get_table_names():
        op.create_table(
            "accounts",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("extra", sa.JSON(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_accounts_id"), "accounts", ["id"], unique=False)

    existing = [c["name"] for c in inspector.get_columns("callers")]
    with op.batch_alter_table("callers", schema=None) as batch_op:
        if "account_id" not in existing:
            batch_op.add_column(sa.Column("account_id", sa.Integer(), nullable=True))
        if "extra" not in existing:
            batch_op.add_column(sa.Column("extra", sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("callers", schema=None) as batch_op:
        batch_op.drop_column("extra")
        batch_op.drop_column("account_id")

    op.drop_index(op.f("ix_accounts_id"), table_name="accounts")
    op.drop_table("accounts")
