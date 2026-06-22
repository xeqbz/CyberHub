from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.modules.matches.model import MatchStatus
from app.modules.teams.schemas import TeamListItem
from app.modules.tournaments.schemas import TournamentListItem


class MatchBase(BaseModel):
    tournament_id: int = Field(..., ge=1)
    home_team_id: int = Field(..., ge=1)
    away_team_id: int = Field(..., ge=1)
    scheduled_at: datetime | None = None
    stage: str = Field(default="Main bracket", min_length=1, max_length=80)
    round_number: int = Field(default=1, ge=1)
    bracket_position: int = Field(default=1, ge=1)

    @staticmethod
    def _validate_teams(home_team_id: int, away_team_id: int) -> None:
        if home_team_id == away_team_id:
            raise ValueError("home_team_id and away_team_id must be different")


class MatchCreate(MatchBase):
    def model_post_init(self, __context) -> None:
        self._validate_teams(self.home_team_id, self.away_team_id)


class MatchUpdate(BaseModel):
    status: MatchStatus | None = None
    scheduled_at: datetime | None = None
    stage: str | None = Field(default=None, min_length=1, max_length=80)
    round_number: int | None = Field(default=None, ge=1)
    bracket_position: int | None = Field(default=None, ge=1)
    home_score: int | None = Field(default=None, ge=0)
    away_score: int | None = Field(default=None, ge=0)
    winner_team_id: int | None = Field(default=None, ge=1)


class MatchScoreUpdate(BaseModel):
    home_score: int = Field(..., ge=0)
    away_score: int = Field(..., ge=0)
    winner_team_id: int | None = Field(default=None, ge=1)


class MatchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tournament_id: int
    home_team_id: int
    away_team_id: int
    status: MatchStatus
    scheduled_at: datetime | None
    completed_at: datetime | None
    stage: str
    round_number: int
    bracket_position: int
    home_score: int | None
    away_score: int | None
    winner_team_id: int | None
    result_confirmed_by_id: int | None
    proposed_home_score: int | None
    proposed_away_score: int | None
    proposed_winner_team_id: int | None
    result_submitted_by_id: int | None
    result_submitted_at: datetime | None
    created_at: datetime
    updated_at: datetime

    tournament: TournamentListItem
    home_team: TeamListItem
    away_team: TeamListItem
    winner_team: TeamListItem | None
    proposed_winner_team: TeamListItem | None


class MatchListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tournament_id: int
    home_team_id: int
    away_team_id: int
    status: MatchStatus
    scheduled_at: datetime | None
    completed_at: datetime | None
    stage: str
    round_number: int
    bracket_position: int
    home_score: int | None
    away_score: int | None
    winner_team_id: int | None
    result_confirmed_by_id: int | None
    proposed_home_score: int | None
    proposed_away_score: int | None
    proposed_winner_team_id: int | None
    result_submitted_by_id: int | None
    result_submitted_at: datetime | None
    created_at: datetime
    updated_at: datetime
