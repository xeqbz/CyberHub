from datetime import datetime
from enum import Enum

from sqlalchemy import CheckConstraint, DateTime, Enum as SqlEnum, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseModel
from app.modules.teams.model import Team
from app.modules.tournaments.model import Tournament


class MatchStatus(str, Enum):
    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class Match(BaseModel):
    __tablename__ = "matches"
    __table_args__ = (
        CheckConstraint("home_team_id <> away_team_id", name="ck_matches_different_teams"),
    )

    tournament_id: Mapped[int] = mapped_column(
        ForeignKey("tournaments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    home_team_id: Mapped[int] = mapped_column(
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    away_team_id: Mapped[int] = mapped_column(
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    status: Mapped[MatchStatus] = mapped_column(
        SqlEnum(MatchStatus, name="match_status"),
        nullable=False,
        default=MatchStatus.SCHEDULED,
    )

    scheduled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    home_score: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    away_score: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    winner_team_id: Mapped[int | None] = mapped_column(
        ForeignKey("teams.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    tournament: Mapped[Tournament] = relationship(
        "Tournament",
        foreign_keys=[tournament_id],
    )
    home_team: Mapped[Team] = relationship(
        "Team",
        foreign_keys=[home_team_id],
    )
    away_team: Mapped[Team] = relationship(
        "Team",
        foreign_keys=[away_team_id],
    )
    winner_team: Mapped[Team | None] = relationship(
        "Team",
        foreign_keys=[winner_team_id],
    )