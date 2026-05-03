from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.modules.matches.model import Match
from app.modules.tournaments.model import Tournament


class MatchRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, match_id: int) -> Match | None:
        stmt = (
            select(Match)
            .where(Match.id == match_id)
            .options(
                joinedload(Match.tournament),
                joinedload(Match.home_team),
                joinedload(Match.away_team),
                joinedload(Match.winner_team),
            )
        )
        return self.db.scalar(stmt)

    def list_matches(self, offset: int = 0, limit: int = 100) -> list[Match]:
        stmt = (
            select(Match)
            .options(
                joinedload(Match.tournament),
                joinedload(Match.home_team),
                joinedload(Match.away_team),
                joinedload(Match.winner_team),
            )
            .order_by(Match.id)
            .offset(offset)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).unique().all())

    def list_by_tournament(self, tournament_id: int) -> list[Match]:
        stmt = (
            select(Match)
            .where(Match.tournament_id == tournament_id)
            .options(
                joinedload(Match.tournament),
                joinedload(Match.home_team),
                joinedload(Match.away_team),
                joinedload(Match.winner_team),
            )
            .order_by(Match.id)
        )
        return list(self.db.scalars(stmt).unique().all())

    def create(
        self,
        *,
        tournament_id: int,
        home_team_id: int,
        away_team_id: int,
        status,
        scheduled_at,
        stage: str,
        round_number: int,
        bracket_position: int,
        home_score: int | None = None,
        away_score: int | None = None,
        winner_team_id: int | None = None,
        result_confirmed_by_id: int | None = None,
        completed_at=None,
    ) -> Match:
        match = Match(
            tournament_id=tournament_id,
            home_team_id=home_team_id,
            away_team_id=away_team_id,
            status=status,
            scheduled_at=scheduled_at,
            stage=stage,
            round_number=round_number,
            bracket_position=bracket_position,
            home_score=home_score,
            away_score=away_score,
            winner_team_id=winner_team_id,
            result_confirmed_by_id=result_confirmed_by_id,
            completed_at=completed_at,
        )
        self.db.add(match)
        self.db.commit()
        self.db.refresh(match)
        return match

    def update(
        self,
        match: Match,
        *,
        status=None,
        scheduled_at=None,
        stage: str | None = None,
        round_number: int | None = None,
        bracket_position: int | None = None,
        home_score: int | None = None,
        away_score: int | None = None,
        winner_team_id: int | None = None,
        result_confirmed_by_id: int | None = None,
        completed_at=None,
        completed_at_was_provided: bool = False,
    ) -> Match:
        if status is not None:
            match.status = status
        if scheduled_at is not None:
            match.scheduled_at = scheduled_at
        if stage is not None:
            match.stage = stage
        if round_number is not None:
            match.round_number = round_number
        if bracket_position is not None:
            match.bracket_position = bracket_position
        if home_score is not None:
            match.home_score = home_score
        if away_score is not None:
            match.away_score = away_score

        match.winner_team_id = winner_team_id
        if result_confirmed_by_id is not None:
            match.result_confirmed_by_id = result_confirmed_by_id
        if completed_at_was_provided:
            match.completed_at = completed_at

        self.db.add(match)
        self.db.commit()
        self.db.refresh(match)
        return match

    def delete(self, match: Match) -> None:
        self.db.delete(match)
        self.db.commit()

    def tournament_exists(self, tournament_id: int) -> bool:
        stmt = select(Tournament.id).where(Tournament.id == tournament_id)
        return self.db.scalar(stmt) is not None
