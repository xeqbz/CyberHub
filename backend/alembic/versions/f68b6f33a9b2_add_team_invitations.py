"""add team invitations

Revision ID: f68b6f33a9b2
Revises: e4a3d9c8b7f1
Create Date: 2026-05-27 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "f68b6f33a9b2"
down_revision: Union[str, Sequence[str], None] = "e4a3d9c8b7f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


team_invitation_status = postgresql.ENUM(
    "PENDING",
    "ACCEPTED",
    "DECLINED",
    name="team_invitation_status",
    create_type=False,
)


def upgrade() -> None:
    """Upgrade schema."""
    postgresql.ENUM(
        "PENDING",
        "ACCEPTED",
        "DECLINED",
        name="team_invitation_status",
    ).create(op.get_bind(), checkfirst=True)
    op.create_table(
        "team_invitations",
        sa.Column("team_id", sa.Integer(), nullable=False),
        sa.Column("invited_user_id", sa.Integer(), nullable=False),
        sa.Column("invited_by_id", sa.Integer(), nullable=True),
        sa.Column(
            "role",
            postgresql.ENUM(
                "OWNER",
                "MEMBER",
                name="team_member_role",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            team_invitation_status,
            nullable=False,
        ),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["invited_by_id"],
            ["users.id"],
            name=op.f("fk_team_invitations_invited_by_id_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["invited_user_id"],
            ["users.id"],
            name=op.f("fk_team_invitations_invited_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["team_id"],
            ["teams.id"],
            name=op.f("fk_team_invitations_team_id_teams"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_team_invitations")),
    )
    op.create_index(
        op.f("ix_team_invitations_invited_by_id"),
        "team_invitations",
        ["invited_by_id"],
    )
    op.create_index(
        op.f("ix_team_invitations_invited_user_id"),
        "team_invitations",
        ["invited_user_id"],
    )
    op.create_index(
        op.f("ix_team_invitations_status"),
        "team_invitations",
        ["status"],
    )
    op.create_index(
        op.f("ix_team_invitations_team_id"),
        "team_invitations",
        ["team_id"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_team_invitations_team_id"), table_name="team_invitations")
    op.drop_index(op.f("ix_team_invitations_status"), table_name="team_invitations")
    op.drop_index(
        op.f("ix_team_invitations_invited_user_id"),
        table_name="team_invitations",
    )
    op.drop_index(
        op.f("ix_team_invitations_invited_by_id"),
        table_name="team_invitations",
    )
    op.drop_table("team_invitations")
    team_invitation_status.drop(op.get_bind(), checkfirst=True)
