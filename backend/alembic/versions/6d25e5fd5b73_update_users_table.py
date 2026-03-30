"""update users table

Revision ID: 6d25e5fd5b73
Revises: 0ce6cd5f9212
Create Date: 2026-03-20 18:18:40.190201
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "6d25e5fd5b73"
down_revision: Union[str, Sequence[str], None] = "0ce6cd5f9212"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


user_role_enum = sa.Enum(
    "USER",
    "ADMIN",
    "ORGANIZER",
    name="user_role",
)


def upgrade() -> None:
    bind = op.get_bind()

    user_role_enum.create(bind, checkfirst=True)

    op.add_column(
        "users",
        sa.Column(
            "hashed_password",
            sa.String(length=255),
            nullable=False,
            server_default="temporary_hash",
        ),
    )

    op.add_column(
        "users",
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )

    op.add_column(
        "users",
        sa.Column(
            "role",
            user_role_enum,
            nullable=False,
            server_default="USER",
        ),
    )

    op.alter_column(
        "users",
        "email",
        existing_type=sa.VARCHAR(length=50),
        type_=sa.String(length=255),
        existing_nullable=False,
    )

    op.drop_constraint(op.f("uq_users_email"), "users", type_="unique")
    op.drop_constraint(op.f("uq_users_username"), "users", type_="unique")

    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)

    op.alter_column("users", "hashed_password", server_default=None)
    op.alter_column("users", "is_active", server_default=None)
    op.alter_column("users", "role", server_default=None)


def downgrade() -> None:
    op.drop_index(op.f("ix_users_username"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")

    op.create_unique_constraint(
        op.f("uq_users_username"),
        "users",
        ["username"],
        postgresql_nulls_not_distinct=False,
    )
    op.create_unique_constraint(
        op.f("uq_users_email"),
        "users",
        ["email"],
        postgresql_nulls_not_distinct=False,
    )

    op.alter_column(
        "users",
        "email",
        existing_type=sa.String(length=255),
        type_=sa.VARCHAR(length=50),
        existing_nullable=False,
    )

    op.drop_column("users", "role")
    op.drop_column("users", "is_active")
    op.drop_column("users", "hashed_password")

    bind = op.get_bind()
    user_role_enum.drop(bind, checkfirst=True)