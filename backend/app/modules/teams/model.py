from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SqlEnum
from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseModel
from app.modules.users.model import User


class TeamMemberRole(str, Enum):
    OWNER = "OWNER"
    MEMBER = "MEMBER"


class TeamInvitationStatus(str, Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    DECLINED = "DECLINED"


class Team(BaseModel):
    __tablename__ = "teams"

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    owner: Mapped[User] = relationship(
        "User",
        foreign_keys=[owner_id],
    )
    members: Mapped[list["TeamMember"]] = relationship(
        "TeamMember",
        back_populates="team",
        cascade="all, delete-orphan",
    )


class TeamMember(BaseModel):
    __tablename__ = "team_members"
    __table_args__ = (
        UniqueConstraint("team_id", "user_id", name="uq_team_members_team_id_user_id"),
    )

    team_id: Mapped[int] = mapped_column(
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[TeamMemberRole] = mapped_column(
        SqlEnum(TeamMemberRole, name="team_member_role"),
        nullable=False,
        default=TeamMemberRole.MEMBER,
    )
    team: Mapped[Team] = relationship(
        "Team",
        back_populates="members",
    )
    user: Mapped[User] = relationship(
        "User",
        foreign_keys=[user_id],
    )


class TeamInvitation(BaseModel):
    __tablename__ = "team_invitations"

    team_id: Mapped[int] = mapped_column(
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    invited_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    invited_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    role: Mapped[TeamMemberRole] = mapped_column(
        SqlEnum(TeamMemberRole, name="team_member_role"),
        nullable=False,
        default=TeamMemberRole.MEMBER,
    )
    status: Mapped[TeamInvitationStatus] = mapped_column(
        SqlEnum(TeamInvitationStatus, name="team_invitation_status"),
        nullable=False,
        default=TeamInvitationStatus.PENDING,
        index=True,
    )
    decided_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    team: Mapped[Team] = relationship("Team", foreign_keys=[team_id])
    invited_user: Mapped[User] = relationship(
        "User",
        foreign_keys=[invited_user_id],
    )
    invited_by: Mapped[User | None] = relationship(
        "User",
        foreign_keys=[invited_by_id],
    )
