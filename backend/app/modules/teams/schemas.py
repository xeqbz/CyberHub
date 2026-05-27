from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.teams.model import TeamInvitationStatus, TeamMemberRole
from app.modules.users.schemas import UserRead


class TeamBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    description: str | None = Field(None, max_length=1000)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return value.strip()

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        return value or None


class TeamCreate(TeamBase):
    pass


class TeamUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=3, max_length=100)
    description: str | None = Field(default=None, max_length=1000)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return value.strip()

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        return value or None


class TeamMemberRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    team_id: int
    user_id: int
    role: TeamMemberRole
    created_at: datetime
    updated_at: datetime
    user: UserRead


class TeamInvitationCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    role: TeamMemberRole = TeamMemberRole.MEMBER

    @field_validator("username", mode="before")
    @classmethod
    def normalize_username(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value


class TeamInvitationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    team_id: int
    invited_user_id: int
    invited_by_id: int | None
    role: TeamMemberRole
    status: TeamInvitationStatus
    decided_at: datetime | None
    created_at: datetime
    updated_at: datetime
    team: "TeamListItem"
    invited_user: UserRead
    invited_by: UserRead | None


class TeamRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    owner_id: int
    created_at: datetime
    updated_at: datetime
    owner: UserRead
    members: list[TeamMemberRead]


class TeamListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    owner_id: int
    created_at: datetime
    updated_at: datetime
