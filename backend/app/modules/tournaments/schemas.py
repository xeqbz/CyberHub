from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.teams.schemas import TeamListItem
from app.modules.tournaments.model import (
    TournamentParticipantStatus,
    TournamentStatus,
)
from app.modules.users.schemas import UserRead


class TournamentBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=150)
    description: str | None = Field(default=None, max_length=2000)
    format: str = Field(default="single_elimination", min_length=3, max_length=80)
    discipline: str = Field(default="CS2", min_length=2, max_length=120)
    rules: str = Field(default="Standard competitive rules", min_length=3)
    bracket_settings: dict | None = None
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

    @field_validator("format", "discipline", "rules")
    @classmethod
    def normalize_required_text(cls, value: str) -> str:
        return value.strip()


class TournamentCreate(TournamentBase):
    status: TournamentStatus = TournamentStatus.DRAFT


class TournamentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=3, max_length=150)
    description: str | None = Field(default=None, max_length=2000)
    format: str | None = Field(default=None, min_length=3, max_length=80)
    discipline: str | None = Field(default=None, min_length=2, max_length=120)
    rules: str | None = Field(default=None, min_length=3)
    bracket_settings: dict | None = None
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

    @field_validator("format", "discipline", "rules")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return value.strip()


class TournamentParticipantReview(BaseModel):
    status: TournamentParticipantStatus


class TournamentParticipantCreate(BaseModel):
    team_id: int = Field(..., ge=1)


class TournamentParticipantRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tournament_id: int
    team_id: int
    status: TournamentParticipantStatus
    decided_by_id: int | None
    decided_at: datetime | None
    created_at: datetime
    updated_at: datetime
    team: TeamListItem


class TournamentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    format: str
    discipline: str
    rules: str
    bracket_settings: dict | None
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
    format: str
    discipline: str
    rules: str
    bracket_settings: dict | None
    status: TournamentStatus
    owner_id: int
    max_teams: int
    starts_at: datetime | None
    created_at: datetime
    updated_at: datetime
