from datetime import datetime
from enum import Enum

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseModel
from app.modules.matches.model import Match
from app.modules.users.model import User


class RankedMatchStatus(str, Enum):
    SCHEDULED = "SCHEDULED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class MatchmakingRequestStatus(str, Enum):
    SEARCHING = "SEARCHING"
    MATCHED = "MATCHED"
    CANCELLED = "CANCELLED"


class DisputeStatus(str, Enum):
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"
    REJECTED = "REJECTED"


class ActionLog(BaseModel):
    __tablename__ = "action_logs"

    actor_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    actor: Mapped[User | None] = relationship("User", foreign_keys=[actor_id])


class Notification(BaseModel):
    __tablename__ = "notifications"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    related_entity_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    related_entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    user: Mapped[User] = relationship("User", foreign_keys=[user_id])


class MatchDispute(BaseModel):
    __tablename__ = "match_disputes"

    match_id: Mapped[int] = mapped_column(
        ForeignKey("matches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    opened_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[DisputeStatus] = mapped_column(
        SqlEnum(DisputeStatus, name="dispute_status"),
        nullable=False,
        default=DisputeStatus.OPEN,
        index=True,
    )
    resolution: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    match: Mapped[Match] = relationship("Match", foreign_keys=[match_id])
    opened_by: Mapped[User] = relationship("User", foreign_keys=[opened_by_id])
    resolved_by: Mapped[User | None] = relationship(
        "User",
        foreign_keys=[resolved_by_id],
    )


class RankedMatch(BaseModel):
    __tablename__ = "ranked_matches"

    discipline: Mapped[str] = mapped_column(
        String(120),
        default="CS2",
        nullable=False,
        index=True,
    )
    mode: Mapped[str] = mapped_column(
        String(40),
        default="1v1",
        nullable=False,
        index=True,
    )
    player_one_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    player_two_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[RankedMatchStatus] = mapped_column(
        SqlEnum(RankedMatchStatus, name="ranked_match_status"),
        nullable=False,
        default=RankedMatchStatus.SCHEDULED,
        index=True,
    )
    player_one_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    player_two_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    player_one_kills: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    player_one_deaths: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    player_one_assists: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    player_two_kills: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    player_two_deaths: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    player_two_assists: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    winner_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    player_one: Mapped[User] = relationship("User", foreign_keys=[player_one_id])
    player_two: Mapped[User] = relationship("User", foreign_keys=[player_two_id])
    winner: Mapped[User | None] = relationship("User", foreign_keys=[winner_id])

    @staticmethod
    def calculate_kda(kills: int, deaths: int, assists: int) -> float:
        return round((kills + assists) / max(deaths, 1), 2)

    @property
    def player_one_kda(self) -> float:
        return self.calculate_kda(
            self.player_one_kills or 0,
            self.player_one_deaths or 0,
            self.player_one_assists or 0,
        )

    @property
    def player_two_kda(self) -> float:
        return self.calculate_kda(
            self.player_two_kills or 0,
            self.player_two_deaths or 0,
            self.player_two_assists or 0,
        )


class MatchmakingRequest(BaseModel):
    __tablename__ = "matchmaking_requests"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[MatchmakingRequestStatus] = mapped_column(
        SqlEnum(MatchmakingRequestStatus, name="matchmaking_request_status"),
        nullable=False,
        default=MatchmakingRequestStatus.SEARCHING,
        index=True,
    )
    discipline: Mapped[str] = mapped_column(
        String(120),
        default="CS2",
        nullable=False,
        index=True,
    )
    mode: Mapped[str] = mapped_column(
        String(40),
        default="1v1",
        nullable=False,
        index=True,
    )
    rating_snapshot: Mapped[int] = mapped_column(Integer, nullable=False)
    matched_ranked_match_id: Mapped[int | None] = mapped_column(
        ForeignKey("ranked_matches.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    user: Mapped[User] = relationship("User", foreign_keys=[user_id])
    matched_ranked_match: Mapped[RankedMatch | None] = relationship(
        "RankedMatch",
        foreign_keys=[matched_ranked_match_id],
    )
