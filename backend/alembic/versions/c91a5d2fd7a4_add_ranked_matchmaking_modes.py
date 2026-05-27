"""add ranked matchmaking modes

Revision ID: c91a5d2fd7a4
Revises: f68b6f33a9b2
Create Date: 2026-05-27 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c91a5d2fd7a4"
down_revision: Union[str, Sequence[str], None] = "f68b6f33a9b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "ranked_matches",
        sa.Column(
            "discipline",
            sa.String(length=120),
            server_default="CS2",
            nullable=False,
        ),
    )
    op.add_column(
        "ranked_matches",
        sa.Column("mode", sa.String(length=40), server_default="1v1", nullable=False),
    )
    op.add_column(
        "matchmaking_requests",
        sa.Column(
            "discipline",
            sa.String(length=120),
            server_default="CS2",
            nullable=False,
        ),
    )
    op.add_column(
        "matchmaking_requests",
        sa.Column("mode", sa.String(length=40), server_default="1v1", nullable=False),
    )

    op.create_index(
        op.f("ix_ranked_matches_discipline"),
        "ranked_matches",
        ["discipline"],
    )
    op.create_index(op.f("ix_ranked_matches_mode"), "ranked_matches", ["mode"])
    op.create_index(
        op.f("ix_matchmaking_requests_discipline"),
        "matchmaking_requests",
        ["discipline"],
    )
    op.create_index(
        op.f("ix_matchmaking_requests_mode"),
        "matchmaking_requests",
        ["mode"],
    )

    op.alter_column("ranked_matches", "discipline", server_default=None)
    op.alter_column("ranked_matches", "mode", server_default=None)
    op.alter_column("matchmaking_requests", "discipline", server_default=None)
    op.alter_column("matchmaking_requests", "mode", server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_matchmaking_requests_mode"), table_name="matchmaking_requests")
    op.drop_index(
        op.f("ix_matchmaking_requests_discipline"),
        table_name="matchmaking_requests",
    )
    op.drop_index(op.f("ix_ranked_matches_mode"), table_name="ranked_matches")
    op.drop_index(op.f("ix_ranked_matches_discipline"), table_name="ranked_matches")
    op.drop_column("matchmaking_requests", "mode")
    op.drop_column("matchmaking_requests", "discipline")
    op.drop_column("ranked_matches", "mode")
    op.drop_column("ranked_matches", "discipline")
