"""create users table

Revision ID: 20260422_0001
Revises:
Create Date: 2026-04-22 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260422_0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("age", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("avatar_url", sa.String(length=2048), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_users_id", "users", ["id"], unique=False)
    op.create_index("ix_users_name", "users", ["name"], unique=False)
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_deleted_at", "users", ["deleted_at"], unique=False)
    op.create_index("ix_users_deleted_at_id", "users", ["deleted_at", "id"], unique=False)

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
        op.execute(
            "CREATE INDEX ix_users_name_trgm_lower ON users USING gin (lower(name) gin_trgm_ops)"
        )
        op.execute(
            "CREATE INDEX ix_users_email_trgm_lower ON users USING gin (lower(email) gin_trgm_ops)"
        )
        op.execute("CREATE INDEX ix_users_name_lower ON users (lower(name))")
        op.execute("CREATE INDEX ix_users_email_lower ON users (lower(email))")


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("DROP INDEX IF EXISTS ix_users_email_lower")
        op.execute("DROP INDEX IF EXISTS ix_users_name_lower")
        op.execute("DROP INDEX IF EXISTS ix_users_email_trgm_lower")
        op.execute("DROP INDEX IF EXISTS ix_users_name_trgm_lower")

    op.drop_index("ix_users_deleted_at_id", table_name="users")
    op.drop_index("ix_users_deleted_at", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_name", table_name="users")
    op.drop_index("ix_users_id", table_name="users")
    op.drop_table("users")
