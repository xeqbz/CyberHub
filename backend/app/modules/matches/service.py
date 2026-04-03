from app.modules.matches.model import Match, MatchStatus
from app.modules.matches.repository import MatchRepository
from app.modules.matches.schemas import MatchCreate, MatchScoreUpdate, MatchUpdate
from app.modules.teams.repository import TeamRepository
from app.modules.tournaments.model import Tournament
from app.modules.tournaments.repository import TournamentRepository


class MatchError(Exception):
    pass


class MatchNotFoundError(MatchError):
    pass


class MatchAccessDeniedError(MatchError):
    pass


class MatchTournamentNotFoundError(MatchError):
    pass


class MatchTeamNotFoundError(MatchError):
    pass


class MatchTeamsMustBeDifferentError(MatchError):
    pass


class MatchTeamNotInTournamentError(MatchError):
    pass


class MatchInvalidWinnerError(MatchError):
    pass


class MatchInvalidScoreError(MatchError):
    pass


class MatchService:
    def __init__(
        self,
        repository: MatchRepository,
        tournament_repository: TournamentRepository,
        team_repository: TeamRepository,
    ) -> None:
        self.repository = repository
        self.tournament_repository = tournament_repository
        self.team_repository = team_repository

    def get_match_by_id(self, match_id: int) -> Match | None:
        return self.repository.get_by_id(match_id)

    def get_match_or_raise(self, match_id: int) -> Match:
        match = self.repository.get_by_id(match_id)
        if match is None:
            raise MatchNotFoundError("Match not found")
        return match

    def list_matches(self, offset: int = 0, limit: int = 100) -> list[Match]:
        return self.repository.list_matches(offset=offset, limit=limit)

    def list_tournament_matches(self, tournament_id: int) -> list[Match]:
        tournament = self.tournament_repository.get_by_id(tournament_id)
        if tournament is None:
            raise MatchTournamentNotFoundError("Tournament not found")
        return self.repository.list_by_tournament(tournament_id)

    def create_match(self, data: MatchCreate, acting_user_id: int) -> Match:
        tournament = self._get_tournament_or_raise(data.tournament_id)
        self._ensure_tournament_owner_access(tournament, acting_user_id)

        self._validate_teams_exist(data.home_team_id, data.away_team_id)
        self._validate_teams_are_different(data.home_team_id, data.away_team_id)
        self._validate_team_registered_in_tournament(data.tournament_id, data.home_team_id)
        self._validate_team_registered_in_tournament(data.tournament_id, data.away_team_id)

        match = self.repository.create(
            tournament_id=data.tournament_id,
            home_team_id=data.home_team_id,
            away_team_id=data.away_team_id,
            status=MatchStatus.SCHEDULED,
            scheduled_at=data.scheduled_at,
            home_score=None,
            away_score=None,
            winner_team_id=None,
        )

        return self.get_match_or_raise(match.id)

    def update_match(
        self,
        match_id: int,
        acting_user_id: int,
        data: MatchUpdate,
    ) -> Match:
        match = self.get_match_or_raise(match_id)
        tournament = self._get_tournament_or_raise(match.tournament_id)
        self._ensure_tournament_owner_access(tournament, acting_user_id)

        winner_team_id = data.winner_team_id
        status = data.status

        home_score = match.home_score if data.home_score is None else data.home_score
        away_score = match.away_score if data.away_score is None else data.away_score

        scores_were_provided = data.home_score is not None or data.away_score is not None
        if (data.home_score is None) != (data.away_score is None):
            raise MatchInvalidScoreError("Both home_score and away_score must be provided together")

        if scores_were_provided:
            winner_team_id = self._resolve_winner_team_id(
                home_team_id=match.home_team_id,
                away_team_id=match.away_team_id,
                home_score=home_score,
                away_score=away_score,
                winner_team_id=data.winner_team_id,
            )
            if status is None:
                status = MatchStatus.COMPLETED

        if status == MatchStatus.COMPLETED and (home_score is None or away_score is None):
            raise MatchInvalidScoreError("Completed match must have both scores")

        updated_match = self.repository.update(
            match,
            status=status,
            scheduled_at=data.scheduled_at,
            home_score=data.home_score,
            away_score=data.away_score,
            winner_team_id=winner_team_id,
        )

        return self.get_match_or_raise(updated_match.id)

    def update_match_score(
        self,
        match_id: int,
        acting_user_id: int,
        data: MatchScoreUpdate,
    ) -> Match:
        match = self.get_match_or_raise(match_id)
        tournament = self._get_tournament_or_raise(match.tournament_id)
        self._ensure_tournament_owner_access(tournament, acting_user_id)

        winner_team_id = self._resolve_winner_team_id(
            home_team_id=match.home_team_id,
            away_team_id=match.away_team_id,
            home_score=data.home_score,
            away_score=data.away_score,
            winner_team_id=data.winner_team_id,
        )

        updated_match = self.repository.update(
            match,
            status=MatchStatus.COMPLETED,
            home_score=data.home_score,
            away_score=data.away_score,
            winner_team_id=winner_team_id,
        )

        return self.get_match_or_raise(updated_match.id)

    def delete_match(self, match_id: int, acting_user_id: int) -> None:
        match = self.get_match_or_raise(match_id)
        tournament = self._get_tournament_or_raise(match.tournament_id)
        self._ensure_tournament_owner_access(tournament, acting_user_id)
        self.repository.delete(match)

    def _get_tournament_or_raise(self, tournament_id: int) -> Tournament:
        tournament = self.tournament_repository.get_by_id(tournament_id)
        if tournament is None:
            raise MatchTournamentNotFoundError("Tournament not found")
        return tournament

    def _validate_teams_exist(self, home_team_id: int, away_team_id: int) -> None:
        home_team = self.team_repository.get_by_id(home_team_id)
        away_team = self.team_repository.get_by_id(away_team_id)

        if home_team is None:
            raise MatchTeamNotFoundError("Home team not found")
        if away_team is None:
            raise MatchTeamNotFoundError("Away team not found")

    @staticmethod
    def _validate_teams_are_different(home_team_id: int, away_team_id: int) -> None:
        if home_team_id == away_team_id:
            raise MatchTeamsMustBeDifferentError("home_team_id and away_team_id must be different")

    def _validate_team_registered_in_tournament(self, tournament_id: int, team_id: int) -> None:
        participant = self.tournament_repository.get_participant(
            tournament_id=tournament_id,
            team_id=team_id,
        )
        if participant is None:
            raise MatchTeamNotInTournamentError("Team is not registered in this tournament")

    @staticmethod
    def _ensure_tournament_owner_access(tournament: Tournament, acting_user_id: int) -> None:
        if tournament.owner_id != acting_user_id:
            raise MatchAccessDeniedError("Only tournament owner can perform this action")

    @staticmethod
    def _resolve_winner_team_id(
        *,
        home_team_id: int,
        away_team_id: int,
        home_score: int,
        away_score: int,
        winner_team_id: int | None,
    ) -> int | None:
        if winner_team_id is not None and winner_team_id not in {home_team_id, away_team_id}:
            raise MatchInvalidWinnerError("winner_team_id must match one of the match teams")

        if home_score > away_score:
            expected_winner = home_team_id
        elif away_score > home_score:
            expected_winner = away_team_id
        else:
            expected_winner = None

        if winner_team_id is None:
            return expected_winner

        if winner_team_id != expected_winner:
            raise MatchInvalidWinnerError("winner_team_id does not match the provided score")

        return winner_team_id