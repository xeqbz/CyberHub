from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.teams.schemas import TeamListItem
from app.modules.tournaments.model import TournamentStatus
from app.modules.users.schemas import UserRead


class TournamentBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=150)
    description: str | None = Field(default=None, max_length=2000)
    max_teams: int = Field(default=8, ge=2, le=1024)
    starts_at: datetime | None = None

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


class TournamentCreate(TournamentBase):
    status: TournamentStatus = TournamentStatus.DRAFT


class TournamentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=3, max_length=150)
    description: str | None = Field(default=None, max_length=2000)
    status: TournamentStatus | None = None
    max_teams: int | None = Field(default=None, ge=2, le=1024)
    starts_at: datetime | None = None

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


class TournamentParticipantCreate(BaseModel):
    team_id: int = Field(..., ge=1)


class TournamentParticipantRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tournament_id: int
    team_id: int
    created_at: datetime
    updated_at: datetime
    team: TeamListItem


class TournamentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    status: TournamentStatus
    owner_id: int
    max_teams: int
    starts_at: datetime | None
    created_at: datetime
    updated_at: datetime
    owner: UserRead
    participants: list[TournamentParticipantRead]


class TournamentListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    status: TournamentStatus
    owner_id: int
    max_teams: int
    starts_at: datetime | None
    created_at: datetime
    updated_at: datetime
