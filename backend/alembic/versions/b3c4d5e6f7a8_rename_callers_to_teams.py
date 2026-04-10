"""rename callers table to teams and caller_id columns to team_id

Revision ID: b3c4d5e6f7a8
Revises: a1b2c3d4e5f6
Create Date: 2026-04-10

Changes:
- Rename table callers → teams
- Rename FK columns caller_id → team_id in: alarms, calls, companies, customers, invoices, users
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "b3c4d5e6f7a8"
down_revision: Union[str, Sequence[str], None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _rename_col_if_needed(inspector, table: str, old: str, new: str) -> None:
    """Rename column old→new only if old exists and new does not."""
    cols = [c["name"] for c in inspector.get_columns(table)]
    if old in cols and new not in cols:
        with op.batch_alter_table(table, schema=None) as batch_op:
            batch_op.alter_column(old, new_column_name=new)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # Rename table callers → teams (skip if already renamed)
    table_names = sa.inspect(bind).get_table_names()
    if "callers" in table_names and "teams" not in table_names:
        op.rename_table("callers", "teams")

    # Rename FK columns in dependent tables (skip if already renamed)
    for table in ("alarms", "calls", "companies", "customers", "invoices", "users"):
        _rename_col_if_needed(inspector, table, "caller_id", "team_id")


def downgrade() -> None:
    # Reverse column renames
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.alter_column("team_id", new_column_name="caller_id")

    with op.batch_alter_table("invoices", schema=None) as batch_op:
        batch_op.alter_column("team_id", new_column_name="caller_id")

    with op.batch_alter_table("customers", schema=None) as batch_op:
        batch_op.alter_column("team_id", new_column_name="caller_id")

    with op.batch_alter_table("companies", schema=None) as batch_op:
        batch_op.alter_column("team_id", new_column_name="caller_id")

    with op.batch_alter_table("calls", schema=None) as batch_op:
        batch_op.alter_column("team_id", new_column_name="caller_id")

    with op.batch_alter_table("alarms", schema=None) as batch_op:
        batch_op.alter_column("team_id", new_column_name="caller_id")

    # Reverse table rename
    op.rename_table("teams", "callers")
