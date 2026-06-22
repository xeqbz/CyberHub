"""add platform features

Revision ID: b7f6a18c9d25
Revises: d1827d06133b
Create Date: 2026-05-03 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "b7f6a18c9d25"
down_revision: Union[str, Sequence[str], None] = "d1827d06133b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


participant_status = postgresql.ENUM(
    "PENDING",
    "APPROVED",
    "REJECTED",
    name="tournament_participant_status",
    create_type=False,
)
dispute_status = postgresql.ENUM(
    "OPEN",
    "RESOLVED",
    "REJECTED",
    name="dispute_status",
    create_type=False,
)
ranked_match_status = postgresql.ENUM(
    "SCHEDULED",
    "COMPLETED",
    "CANCELLED",
    name="ranked_match_status",
    create_type=False,
)
matchmaking_request_status = postgresql.ENUM(
    "SEARCHING",
    "MATCHED",
    "CANCELLED",
    name="matchmaking_request_status",
    create_type=False,
)


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "users",
        sa.Column("rating", sa.Integer(), server_default="1000", nullable=False),
    )
    op.add_column(
        "users",
        sa.Column("wins", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "users",
        sa.Column("losses", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "users",
        sa.Column("draws", sa.Integer(), server_default="0", nullable=False),
    )
    op.alter_column("users", "rating", server_default=None)
    op.alter_column("users", "wins", server_default=None)
    op.alter_column("users", "losses", server_default=None)
    op.alter_column("users", "draws", server_default=None)

    op.add_column(
        "tournaments",
        sa.Column(
            "format",
            sa.String(length=80),
            server_default="single_elimination",
            nullable=False,
        ),
    )
    op.add_column(
        "tournaments",
        sa.Column("discipline", sa.String(length=120), server_default="CS2", nullable=False),
    )
    op.add_column(
        "tournaments",
        sa.Column(
            "rules",
            sa.Text(),
            server_default="Standard competitive rules",
            nullable=False,
        ),
    )
    op.add_column("tournaments", sa.Column("bracket_settings", sa.JSON(), nullable=True))
    op.alter_column("tournaments", "format", server_default=None)
    op.alter_column("tournaments", "discipline", server_default=None)
    op.alter_column("tournaments", "rules", server_default=None)

    participant_status.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "tournament_participants",
        sa.Column(
            "status",
            participant_status,
            server_default="APPROVED",
            nullable=False,
        ),
    )
    op.add_column(
        "tournament_participants",
        sa.Column("decided_by_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "tournament_participants",
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_foreign_key(
        op.f("fk_tournament_participants_decided_by_id_users"),
        "tournament_participants",
        "users",
        ["decided_by_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        op.f("ix_tournament_participants_decided_by_id"),
        "tournament_participants",
        ["decided_by_id"],
        unique=False,
    )
    op.alter_column("tournament_participants", "status", server_default=None)

    op.add_column("matches", sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "matches",
        sa.Column("stage", sa.String(length=80), server_default="Main bracket", nullable=False),
    )
    op.add_column(
        "matches",
        sa.Column("round_number", sa.Integer(), server_default="1", nullable=False),
    )
    op.add_column(
        "matches",
        sa.Column("bracket_position", sa.Integer(), server_default="1", nullable=False),
    )
    op.add_column("matches", sa.Column("result_confirmed_by_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        op.f("fk_matches_result_confirmed_by_id_users"),
        "matches",
        "users",
        ["result_confirmed_by_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        op.f("ix_matches_result_confirmed_by_id"),
        "matches",
        ["result_confirmed_by_id"],
        unique=False,
    )
    op.alter_column("matches", "stage", server_default=None)
    op.alter_column("matches", "round_number", server_default=None)
    op.alter_column("matches", "bracket_position", server_default=None)

    dispute_status.create(op.get_bind(), checkfirst=True)
    ranked_match_status.create(op.get_bind(), checkfirst=True)
    matchmaking_request_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "action_logs",
        sa.Column("actor_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column("entity_type", sa.String(length=80), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_action_logs")),
    )
    op.create_index(op.f("ix_action_logs_action"), "action_logs", ["action"], unique=False)
    op.create_index(op.f("ix_action_logs_actor_id"), "action_logs", ["actor_id"], unique=False)
    op.create_index(op.f("ix_action_logs_entity_id"), "action_logs", ["entity_id"], unique=False)
    op.create_index(op.f("ix_action_logs_entity_type"), "action_logs", ["entity_type"], unique=False)

    op.create_table(
        "notifications",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False),
        sa.Column("related_entity_type", sa.String(length=80), nullable=True),
        sa.Column("related_entity_id", sa.Integer(), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_notifications")),
    )
    op.create_index(op.f("ix_notifications_user_id"), "notifications", ["user_id"], unique=False)

    op.create_table(
        "match_disputes",
        sa.Column("match_id", sa.Integer(), nullable=False),
        sa.Column("opened_by_id", sa.Integer(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", dispute_status, nullable=False),
        sa.Column("resolution", sa.Text(), nullable=True),
        sa.Column("resolved_by_id", sa.Integer(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["match_id"], ["matches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["opened_by_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["resolved_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_match_disputes")),
    )
    op.create_index(op.f("ix_match_disputes_match_id"), "match_disputes", ["match_id"], unique=False)
    op.create_index(op.f("ix_match_disputes_opened_by_id"), "match_disputes", ["opened_by_id"], unique=False)
    op.create_index(op.f("ix_match_disputes_resolved_by_id"), "match_disputes", ["resolved_by_id"], unique=False)
    op.create_index(op.f("ix_match_disputes_status"), "match_disputes", ["status"], unique=False)

    op.create_table(
        "ranked_matches",
        sa.Column("player_one_id", sa.Integer(), nullable=False),
        sa.Column("player_two_id", sa.Integer(), nullable=False),
        sa.Column("status", ranked_match_status, nullable=False),
        sa.Column("player_one_score", sa.Integer(), nullable=True),
        sa.Column("player_two_score", sa.Integer(), nullable=True),
        sa.Column("winner_id", sa.Integer(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["player_one_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["player_two_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["winner_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ranked_matches")),
    )
    op.create_index(op.f("ix_ranked_matches_player_one_id"), "ranked_matches", ["player_one_id"], unique=False)
    op.create_index(op.f("ix_ranked_matches_player_two_id"), "ranked_matches", ["player_two_id"], unique=False)
    op.create_index(op.f("ix_ranked_matches_status"), "ranked_matches", ["status"], unique=False)
    op.create_index(op.f("ix_ranked_matches_winner_id"), "ranked_matches", ["winner_id"], unique=False)

    op.create_table(
        "matchmaking_requests",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("status", matchmaking_request_status, nullable=False),
        sa.Column("rating_snapshot", sa.Integer(), nullable=False),
        sa.Column("matched_ranked_match_id", sa.Integer(), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["matched_ranked_match_id"], ["ranked_matches.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_matchmaking_requests")),
    )
    op.create_index(op.f("ix_matchmaking_requests_matched_ranked_match_id"), "matchmaking_requests", ["matched_ranked_match_id"], unique=False)
    op.create_index(op.f("ix_matchmaking_requests_status"), "matchmaking_requests", ["status"], unique=False)
    op.create_index(op.f("ix_matchmaking_requests_user_id"), "matchmaking_requests", ["user_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_matchmaking_requests_user_id"), table_name="matchmaking_requests")
    op.drop_index(op.f("ix_matchmaking_requests_status"), table_name="matchmaking_requests")
    op.drop_index(op.f("ix_matchmaking_requests_matched_ranked_match_id"), table_name="matchmaking_requests")
    op.drop_table("matchmaking_requests")

    op.drop_index(op.f("ix_ranked_matches_winner_id"), table_name="ranked_matches")
    op.drop_index(op.f("ix_ranked_matches_status"), table_name="ranked_matches")
    op.drop_index(op.f("ix_ranked_matches_player_two_id"), table_name="ranked_matches")
    op.drop_index(op.f("ix_ranked_matches_player_one_id"), table_name="ranked_matches")
    op.drop_table("ranked_matches")

    op.drop_index(op.f("ix_match_disputes_status"), table_name="match_disputes")
    op.drop_index(op.f("ix_match_disputes_resolved_by_id"), table_name="match_disputes")
    op.drop_index(op.f("ix_match_disputes_opened_by_id"), table_name="match_disputes")
    op.drop_index(op.f("ix_match_disputes_match_id"), table_name="match_disputes")
    op.drop_table("match_disputes")

    op.drop_index(op.f("ix_notifications_user_id"), table_name="notifications")
    op.drop_table("notifications")

    op.drop_index(op.f("ix_action_logs_entity_type"), table_name="action_logs")
    op.drop_index(op.f("ix_action_logs_entity_id"), table_name="action_logs")
    op.drop_index(op.f("ix_action_logs_actor_id"), table_name="action_logs")
    op.drop_index(op.f("ix_action_logs_action"), table_name="action_logs")
    op.drop_table("action_logs")

    matchmaking_request_status.drop(op.get_bind(), checkfirst=True)
    ranked_match_status.drop(op.get_bind(), checkfirst=True)
    dispute_status.drop(op.get_bind(), checkfirst=True)

    op.drop_index(op.f("ix_matches_result_confirmed_by_id"), table_name="matches")
    op.drop_constraint(op.f("fk_matches_result_confirmed_by_id_users"), "matches", type_="foreignkey")
    op.drop_column("matches", "result_confirmed_by_id")
    op.drop_column("matches", "bracket_position")
    op.drop_column("matches", "round_number")
    op.drop_column("matches", "stage")
    op.drop_column("matches", "completed_at")

    op.drop_index(op.f("ix_tournament_participants_decided_by_id"), table_name="tournament_participants")
    op.drop_constraint(
        op.f("fk_tournament_participants_decided_by_id_users"),
        "tournament_participants",
        type_="foreignkey",
    )
    op.drop_column("tournament_participants", "decided_at")
    op.drop_column("tournament_participants", "decided_by_id")
    op.drop_column("tournament_participants", "status")
    participant_status.drop(op.get_bind(), checkfirst=True)

    op.drop_column("tournaments", "bracket_settings")
    op.drop_column("tournaments", "rules")
    op.drop_column("tournaments", "discipline")
    op.drop_column("tournaments", "format")

    op.drop_column("users", "draws")
    op.drop_column("users", "losses")
    op.drop_column("users", "wins")
    op.drop_column("users", "rating")
