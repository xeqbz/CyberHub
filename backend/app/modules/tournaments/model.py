from datetime import datetime
from enum import Enum

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy import Enum as SqlEnum
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


class TournamentParticipantStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


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
    format: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
        default="single_elimination",
    )
    discipline: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
        default="CS2",
    )
    rules: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="Standard competitive rules",
    )
    bracket_settings: Mapped[dict | None] = mapped_column(
        JSON,
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
    status: Mapped[TournamentParticipantStatus] = mapped_column(
        SqlEnum(
            TournamentParticipantStatus,
            name="tournament_participant_status",
        ),
        nullable=False,
        default=TournamentParticipantStatus.PENDING,
    )
    decided_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    decided_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    tournament: Mapped[Tournament] = relationship(
        "Tournament",
        back_populates="participants",
    )
    team: Mapped[Team] = relationship(
        "Team",
        foreign_keys=[team_id],
    )
    decided_by: Mapped[User | None] = relationship(
        "User",
        foreign_keys=[decided_by_id],
    )
