from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SqlEnum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseModel
from app.modules.teams.model import Team
from app.modules.users.model import User


class TournamentStatus(str, Enum):
    DRAFT = "DRAFT"
    REGISTRATION_OPEN = "REGISTRATION_OPEN"
    REGISTRATION_CLOSED = "REGISTRATION_CLOSED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class Tournament(BaseModel):
    __tablename__ = "tournaments"

    name: Mapped[str] = mapped_column(
        String(150),
        unique=True,
        index=True,
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    status: Mapped[TournamentStatus] = mapped_column(
        SqlEnum(TournamentStatus, name="tournament_status"),
        nullable=False,
        default=TournamentStatus.DRAFT,
    )
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    max_teams: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=8,
    )
    starts_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    owner: Mapped[User] = relationship(
        "User",
        foreign_keys=[owner_id],
    )
    participants: Mapped[list["TournamentParticipant"]] = relationship(
        "TournamentParticipant",
        back_populates="tournament",
        cascade="all, delete-orphan",
    )


class TournamentParticipant(BaseModel):
    __tablename__ = "tournament_participants"
    __table_args__ = (
        UniqueConstraint(
            "tournament_id",
            "team_id",
            name="uq_tournament_participants_tournament_id_team_id",
        ),
    )

    tournament_id: Mapped[int] = mapped_column(
        ForeignKey("tournaments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    team_id: Mapped[int] = mapped_column(
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    tournament: Mapped[Tournament] = relationship(
        "Tournament",
        back_populates="participants",
    )
    team: Mapped[Team] = relationship(
        "Team",
        foreign_keys=[team_id],
    )