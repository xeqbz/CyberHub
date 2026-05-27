"""add ranked match player stats

Revision ID: 9fd2df5d3c9e
Revises: b7f6a18c9d25
Create Date: 2026-05-27 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9fd2df5d3c9e"
down_revision: Union[str, Sequence[str], None] = "b7f6a18c9d25"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "ranked_matches",
        sa.Column("player_one_kills", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "ranked_matches",
        sa.Column("player_one_deaths", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "ranked_matches",
        sa.Column("player_one_assists", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "ranked_matches",
        sa.Column("player_two_kills", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "ranked_matches",
        sa.Column("player_two_deaths", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "ranked_matches",
        sa.Column("player_two_assists", sa.Integer(), server_default="0", nullable=False),
    )

    for column_name in (
        "player_one_kills",
        "player_one_deaths",
        "player_one_assists",
        "player_two_kills",
        "player_two_deaths",
        "player_two_assists",
    ):
        op.alter_column("ranked_matches", column_name, server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("ranked_matches", "player_two_assists")
    op.drop_column("ranked_matches", "player_two_deaths")
    op.drop_column("ranked_matches", "player_two_kills")
    op.drop_column("ranked_matches", "player_one_assists")
    op.drop_column("ranked_matches", "player_one_deaths")
    op.drop_column("ranked_matches", "player_one_kills")
