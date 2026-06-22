from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.matches.schemas import MatchRead
from app.modules.platform.model import (
    DisputeStatus,
    MatchmakingRequestStatus,
    RankedMatchStatus,
)
from app.modules.users.schemas import UserRead


class RankingUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    rating: int
    wins: int
    losses: int
    draws: int


class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    title: str
    message: str
    is_read: bool
    related_entity_type: str | None
    related_entity_id: int | None
    created_at: datetime
    updated_at: datetime


class ActionLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    actor_id: int | None
    action: str
    entity_type: str
    entity_id: int | None
    details: dict | None
    created_at: datetime
    updated_at: datetime
    actor: UserRead | None


class MatchDisputeCreate(BaseModel):
    match_id: int = Field(..., ge=1)
    reason: str = Field(..., min_length=5, max_length=2000)


class MatchDisputeResolve(BaseModel):
    status: DisputeStatus = DisputeStatus.RESOLVED
    resolution: str = Field(..., min_length=3, max_length=2000)


class MatchDisputeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    match_id: int
    opened_by_id: int
    reason: str
    status: DisputeStatus
    resolution: str | None
    resolved_by_id: int | None
    resolved_at: datetime | None
    created_at: datetime
    updated_at: datetime
    opened_by: UserRead
    resolved_by: UserRead | None
    match: MatchRead


class RankedMatchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    discipline: str
    mode: str
    player_one_id: int
    player_two_id: int
    status: RankedMatchStatus
    player_one_score: int | None
    player_two_score: int | None
    player_one_kills: int
    player_one_deaths: int
    player_one_assists: int
    player_one_kda: float
    player_two_kills: int
    player_two_deaths: int
    player_two_assists: int
    player_two_kda: float
    winner_id: int | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    player_one: UserRead
    player_two: UserRead
    winner: UserRead | None


class MatchmakingRequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    status: MatchmakingRequestStatus
    discipline: str
    mode: str
    rating_snapshot: int
    matched_ranked_match_id: int | None
    created_at: datetime
    updated_at: datetime


class MatchmakingRequestCreate(BaseModel):
    discipline: str = Field(default="CS2", min_length=1, max_length=120)
    mode: str = Field(default="1v1", min_length=1, max_length=40)
    demo_opponent_username: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
    )

    @field_validator("discipline", "mode", "demo_opponent_username", mode="before")
    @classmethod
    def normalize_label(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value


class MatchmakingResponse(BaseModel):
    status: MatchmakingRequestStatus
    message: str
    request: MatchmakingRequestRead | None = None
    match: RankedMatchRead | None = None
    discipline: str | None = None
    mode: str | None = None
    rating_range: int | None = None


class RankedMatchScoreUpdate(BaseModel):
    player_one_score: int = Field(..., ge=0)
    player_two_score: int = Field(..., ge=0)
    player_one_kills: int = Field(default=0, ge=0)
    player_one_deaths: int = Field(default=0, ge=0)
    player_one_assists: int = Field(default=0, ge=0)
    player_two_kills: int = Field(default=0, ge=0)
    player_two_deaths: int = Field(default=0, ge=0)
    player_two_assists: int = Field(default=0, ge=0)


class OverviewStats(BaseModel):
    users: int
    teams: int
    tournaments: int
    tournament_matches: int
    ranked_matches: int
    open_disputes: int
    completed_matches: int


class TeamStats(BaseModel):
    team_id: int
    name: str
    matches: int
    wins: int
    losses: int
    draws: int


class PlayerStats(BaseModel):
    user_id: int
    username: str
    rating: int
    ranked_matches: int
    wins: int
    losses: int
    draws: int
    kills: int
    deaths: int
    assists: int
    kda: float


class TournamentStats(BaseModel):
    tournament_id: int
    name: str
    discipline: str
    format: str
    participants: int
    matches: int
    completed_matches: int


class ReportRow(BaseModel):
    values: dict


class ProfileTeamSummary(BaseModel):
    id: int
    name: str
    role: str
    created_at: datetime


class ProfileTournamentSummary(BaseModel):
    id: int
    name: str
    status: str
    participant_status: str
    team_name: str
    starts_at: datetime | None


class ProfileMatchSummary(BaseModel):
    id: int
    tournament_id: int
    tournament_name: str
    home_team_name: str
    away_team_name: str
    status: str
    scheduled_at: datetime | None
    completed_at: datetime | None


class ProfileHistory(BaseModel):
    teams: list[ProfileTeamSummary]
    tournaments: list[ProfileTournamentSummary]
    tournament_matches: list[ProfileMatchSummary]
    ranked_matches: list[RankedMatchRead]
