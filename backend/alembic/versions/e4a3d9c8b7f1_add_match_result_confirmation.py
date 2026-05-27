"""add match result confirmation

Revision ID: e4a3d9c8b7f1
Revises: 9fd2df5d3c9e
Create Date: 2026-05-27 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e4a3d9c8b7f1"
down_revision: Union[str, Sequence[str], None] = "9fd2df5d3c9e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        "ALTER TYPE match_status ADD VALUE IF NOT EXISTS 'PENDING_CONFIRMATION'"
    )
    op.execute("ALTER TYPE match_status ADD VALUE IF NOT EXISTS 'DISPUTED'")

    op.add_column("matches", sa.Column("proposed_home_score", sa.Integer()))
    op.add_column("matches", sa.Column("proposed_away_score", sa.Integer()))
    op.add_column("matches", sa.Column("proposed_winner_team_id", sa.Integer()))
    op.add_column("matches", sa.Column("result_submitted_by_id", sa.Integer()))
    op.add_column(
        "matches",
        sa.Column("result_submitted_at", sa.DateTime(timezone=True)),
    )
    op.create_foreign_key(
        op.f("fk_matches_proposed_winner_team_id_teams"),
        "matches",
        "teams",
        ["proposed_winner_team_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        op.f("fk_matches_result_submitted_by_id_users"),
        "matches",
        "users",
        ["result_submitted_by_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        op.f("ix_matches_proposed_winner_team_id"),
        "matches",
        ["proposed_winner_team_id"],
    )
    op.create_index(
        op.f("ix_matches_result_submitted_by_id"),
        "matches",
        ["result_submitted_by_id"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_matches_result_submitted_by_id"), table_name="matches")
    op.drop_index(op.f("ix_matches_proposed_winner_team_id"), table_name="matches")
    op.drop_constraint(
        op.f("fk_matches_result_submitted_by_id_users"),
        "matches",
        type_="foreignkey",
    )
    op.drop_constraint(
        op.f("fk_matches_proposed_winner_team_id_teams"),
        "matches",
        type_="foreignkey",
    )
    op.drop_column("matches", "result_submitted_at")
    op.drop_column("matches", "result_submitted_by_id")
    op.drop_column("matches", "proposed_winner_team_id")
    op.drop_column("matches", "proposed_away_score")
    op.drop_column("matches", "proposed_home_score")
