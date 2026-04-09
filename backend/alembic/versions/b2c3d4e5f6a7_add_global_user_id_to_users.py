"""add global_user_id to users

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Branch Labels: None
Depends On: None

Changes:
- Add global_user_id (nullable int) to users table — references master.global_users.id
- Make password_hash nullable — auth moves to GlobalUser in master DB
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing = [c["name"] for c in inspector.get_columns("users")]

    with op.batch_alter_table("users", schema=None) as batch_op:
        if "global_user_id" not in existing:
            batch_op.add_column(sa.Column("global_user_id", sa.Integer(), nullable=True))
        # Make password_hash nullable (auth moves to master DB)
        batch_op.alter_column("password_hash", existing_type=sa.String(), nullable=True)


def downgrade() -> None:
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.alter_column("password_hash", existing_type=sa.String(), nullable=False)
        batch_op.drop_column("global_user_id")
