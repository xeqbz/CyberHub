from datetime import UTC, datetime

from app.modules.teams.repository import TeamRepository
from app.modules.tournaments.model import (
    Tournament,
    TournamentParticipant,
    TournamentParticipantStatus,
    TournamentStatus,
)
from app.modules.tournaments.repository import TournamentRepository
from app.modules.tournaments.schemas import (
    TournamentCreate,
    TournamentParticipantReview,
    TournamentUpdate,
)


class TournamentError(Exception):
    pass


class TournamentNotFoundError(TournamentError):
    pass


class TournamentAlreadyExistsError(TournamentError):
    pass


class TournamentAccessDeniedError(TournamentError):
    pass


class TournamentRegistrationClosedError(TournamentError):
    pass


class TournamentParticipantAlreadyExistsError(TournamentError):
    pass


class TournamentParticipantNotFoundError(TournamentError):
    pass


class TournamentCapacityExceededError(TournamentError):
    pass


class TournamentLockedError(TournamentError):
    pass


class TournamentTeamNotFoundError(TournamentError):
    pass


class TournamentTeamAccessDeniedError(TournamentError):
    pass


class TournamentService:
    def __init__(
        self,
        repository: TournamentRepository,
        team_repository: TeamRepository,
    ) -> None:
        self.repository = repository
        self.team_repository = team_repository

    def get_tournament_by_id(self, tournament_id: int) -> Tournament | None:
        return self.repository.get_by_id(tournament_id)

    def get_tournament_or_raise(self, tournament_id: int) -> Tournament:
        tournament = self.repository.get_by_id(tournament_id)
        if tournament is None:
            raise TournamentNotFoundError("Tournament not found")
        return tournament

    def get_tournament_by_name(self, name: str) -> Tournament | None:
        return self.repository.get_by_name(name.strip())

    def list_tournaments(self, offset: int = 0, limit: int = 100) -> list[Tournament]:
        return self.repository.list_tournaments(offset=offset, limit=limit)

    def list_owner_tournaments(self, owner_id: int) -> list[Tournament]:
        return self.repository.list_by_owner(owner_id)

    def create_tournament(self, data: TournamentCreate, owner_id: int) -> Tournament:
        normalized_name = data.name.strip()

        existing_tournament = self.repository.get_by_name(normalized_name)
        if existing_tournament is not None:
            raise TournamentAlreadyExistsError(
                "Tournament with this name already exists"
            )

        tournament = self.repository.create(
            name=normalized_name,
            description=data.description,
            status=data.status,
            owner_id=owner_id,
            format=data.format,
            discipline=data.discipline,
            rules=data.rules,
            bracket_settings=data.bracket_settings,
            max_teams=data.max_teams,
            starts_at=data.starts_at,
        )

        return self.get_tournament_or_raise(tournament.id)

    def update_tournament(
        self,
        tournament_id: int,
        acting_user_id: int,
        data: TournamentUpdate,
    ) -> Tournament:
        tournament = self.get_tournament_or_raise(tournament_id)
        self._ensure_owner_access(tournament, acting_user_id)

        normalized_name = data.name.strip() if data.name is not None else None

        if normalized_name is not None and normalized_name != tournament.name:
            existing_tournament = self.repository.get_by_name(normalized_name)
            if (
                existing_tournament is not None
                and existing_tournament.id != tournament.id
            ):
                raise TournamentAlreadyExistsError(
                    "Tournament with this name already exists"
                )

        if data.max_teams is not None:
            current_participants = self.repository.count_participants(tournament.id)
            if data.max_teams < current_participants:
                raise TournamentCapacityExceededError(
                    "max_teams cannot be less than the current number of participants"
                )

        is_rules_change = any(
            field in data.model_fields_set
            for field in {"format", "discipline", "rules", "bracket_settings"}
        )
        if is_rules_change and tournament.status in {
            TournamentStatus.IN_PROGRESS,
            TournamentStatus.COMPLETED,
        }:
            raise TournamentLockedError(
                "Tournament rules and bracket settings cannot be changed after start"
            )

        updated_tournament = self.repository.update(
            tournament,
            name=normalized_name,
            description=data.description,
            format=data.format,
            discipline=data.discipline,
            rules=data.rules,
            bracket_settings=data.bracket_settings,
            bracket_settings_was_provided="bracket_settings" in data.model_fields_set,
            status=data.status,
            max_teams=data.max_teams,
            starts_at=data.starts_at,
        )

        return self.get_tournament_or_raise(updated_tournament.id)

    def delete_tournament(self, tournament_id: int, acting_user_id: int) -> None:
        tournament = self.get_tournament_or_raise(tournament_id)
        self._ensure_owner_access(tournament, acting_user_id)
        self.repository.delete(tournament)

    def list_participants(self, tournament_id: int) -> list[TournamentParticipant]:
        tournament = self.get_tournament_or_raise(tournament_id)
        return self.repository.list_participants(tournament.id)

    def add_participant(
        self,
        tournament_id: int,
        team_id: int,
        acting_user_id: int,
    ) -> TournamentParticipant:
        tournament = self.get_tournament_or_raise(tournament_id)

        if tournament.status != TournamentStatus.REGISTRATION_OPEN:
            raise TournamentRegistrationClosedError(
                "Tournament registration is not open"
            )

        team = self.team_repository.get_by_id(team_id)
        if team is None:
            raise TournamentTeamNotFoundError("Team not found")

        if team.owner_id != acting_user_id and tournament.owner_id != acting_user_id:
            raise TournamentTeamAccessDeniedError(
                "Only team owner or tournament owner can register the team"
            )

        existing_participant = self.repository.get_participant(
            tournament_id=tournament.id,
            team_id=team_id,
        )
        if existing_participant is not None:
            raise TournamentParticipantAlreadyExistsError(
                "Team is already registered in this tournament"
            )

        current_participants = self.repository.count_participants(tournament.id)
        if current_participants >= tournament.max_teams:
            raise TournamentCapacityExceededError(
                "Tournament participant limit has been reached"
            )

        participant_status = (
            TournamentParticipantStatus.APPROVED
            if tournament.owner_id == acting_user_id
            else TournamentParticipantStatus.PENDING
        )
        decided_by_id = (
            acting_user_id
            if participant_status == TournamentParticipantStatus.APPROVED
            else None
        )
        decided_at = (
            datetime.now(UTC)
            if participant_status == TournamentParticipantStatus.APPROVED
            else None
        )

        return self.repository.add_participant(
            tournament_id=tournament.id,
            team_id=team_id,
            status=participant_status,
            decided_by_id=decided_by_id,
            decided_at=decided_at,
        )

    def remove_participant(
        self,
        tournament_id: int,
        team_id: int,
        acting_user_id: int,
    ) -> None:
        tournament = self.get_tournament_or_raise(tournament_id)

        participant = self.repository.get_participant(
            tournament_id=tournament.id,
            team_id=team_id,
        )
        if participant is None:
            raise TournamentParticipantNotFoundError("Tournament participant not found")

        team = self.team_repository.get_by_id(team_id)
        if team is None:
            raise TournamentTeamNotFoundError("Team not found")

        if team.owner_id != acting_user_id and tournament.owner_id != acting_user_id:
            raise TournamentTeamAccessDeniedError(
                "Only team owner or tournament owner can remove the team"
            )

        self.repository.remove_participant(participant)

    def review_participant(
        self,
        tournament_id: int,
        team_id: int,
        acting_user_id: int,
        data: TournamentParticipantReview,
    ) -> TournamentParticipant:
        tournament = self.get_tournament_or_raise(tournament_id)
        self._ensure_owner_access(tournament, acting_user_id)

        participant = self.repository.get_participant(
            tournament_id=tournament.id,
            team_id=team_id,
        )
        if participant is None:
            raise TournamentParticipantNotFoundError("Tournament participant not found")

        if data.status == TournamentParticipantStatus.APPROVED:
            current_participants = self.repository.count_participants(tournament.id)
            if (
                participant.status != TournamentParticipantStatus.APPROVED
                and current_participants >= tournament.max_teams
            ):
                raise TournamentCapacityExceededError(
                    "Tournament participant limit has been reached"
                )

        return self.repository.update_participant(
            participant,
            status=data.status,
            decided_by_id=acting_user_id,
            decided_at=datetime.now(UTC),
        )

    @staticmethod
    def _ensure_owner_access(tournament: Tournament, acting_user_id: int) -> None:
        if tournament.owner_id != acting_user_id:
            raise TournamentAccessDeniedError(
                "Only tournament owner can perform this action"
            )
