from datetime import UTC, datetime
from math import ceil, log2

from app.modules.matches.model import Match, MatchStatus
from app.modules.matches.repository import MatchRepository
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


BRACKET_STATE_KEY = "_cyberhub_bracket"
DOUBLE_UPPER_STAGE = "Upper bracket"
DOUBLE_LOWER_STAGE = "Lower bracket"
DOUBLE_GRAND_FINAL_STAGE = "Grand final"
MAIN_BRACKET_STAGE = "Main bracket"
ROUND_ROBIN_STAGE = "Round robin"
SWISS_STAGE = "Swiss"


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


class TournamentBracketAlreadyExistsError(TournamentError):
    pass


class TournamentBracketNotReadyError(TournamentError):
    pass


class TournamentUnsupportedFormatError(TournamentError):
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
        match_repository: MatchRepository,
    ) -> None:
        self.repository = repository
        self.team_repository = team_repository
        self.match_repository = match_repository

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

    def generate_bracket(
        self,
        tournament_id: int,
        acting_user_id: int,
    ) -> list[Match]:
        tournament = self.get_tournament_or_raise(tournament_id)
        self._ensure_owner_access(tournament, acting_user_id)

        if tournament.status not in {
            TournamentStatus.REGISTRATION_CLOSED,
            TournamentStatus.IN_PROGRESS,
        }:
            raise TournamentBracketNotReadyError(
                "Close registration before generating the bracket"
            )

        if self.match_repository.list_by_tournament(tournament.id):
            raise TournamentBracketAlreadyExistsError(
                "Tournament already has generated or manually created matches"
            )

        participants = [
            participant
            for participant in self.repository.list_participants(tournament.id)
            if participant.status == TournamentParticipantStatus.APPROVED
        ]

        if len(participants) < 2:
            raise TournamentBracketNotReadyError(
                "At least two approved participants are required"
            )

        ordered_participants = self._sort_participants_for_bracket(
            tournament,
            participants,
        )
        tournament_format = self._normalize_format(tournament.format)

        if tournament_format == "single_elimination":
            self._generate_single_elimination_matches(
                tournament=tournament,
                participants=ordered_participants,
            )
        elif tournament_format == "double_elimination":
            self._generate_double_elimination_matches(
                tournament=tournament,
                participants=ordered_participants,
            )
        elif tournament_format == "round_robin":
            self._generate_round_robin_matches(
                tournament=tournament,
                participants=ordered_participants,
            )
        elif tournament_format == "swiss":
            self._generate_swiss_matches(
                tournament=tournament,
                participants=ordered_participants,
            )
        else:
            raise TournamentUnsupportedFormatError(
                f"Tournament format '{tournament.format}' is not supported yet"
            )

        return self.match_repository.list_by_tournament(tournament.id)

    def _generate_single_elimination_matches(
        self,
        *,
        tournament: Tournament,
        participants: list[TournamentParticipant],
    ) -> None:
        if not self._is_power_of_two(len(participants)):
            raise TournamentBracketNotReadyError(
                "Single-elimination bracket requires a power-of-two number of "
                "approved participants"
            )

        rounds = self._playoff_rounds(len(participants))
        state = self._new_playoff_state(
            tournament_format="single_elimination",
            rounds=rounds,
        )
        midpoint = len(participants) // 2
        first_half = participants[:midpoint]
        second_half = list(reversed(participants[midpoint:]))

        for position, (home, away) in enumerate(
            zip(first_half, second_half),
            start=1,
        ):
            match = self.match_repository.create(
                tournament_id=tournament.id,
                home_team_id=home.team_id,
                away_team_id=away.team_id,
                status=MatchStatus.SCHEDULED,
                scheduled_at=None,
                stage=MAIN_BRACKET_STAGE,
                round_number=1,
                bracket_position=position,
            )
            self._register_playoff_advancement(
                state,
                match,
                tournament_format="single_elimination",
                rounds=rounds,
            )

        self._save_bracket_state(tournament, state)

    def _generate_double_elimination_matches(
        self,
        *,
        tournament: Tournament,
        participants: list[TournamentParticipant],
    ) -> None:
        if len(participants) < 4 or not self._is_power_of_two(len(participants)):
            raise TournamentBracketNotReadyError(
                "Double-elimination bracket requires at least four approved "
                "participants and a power-of-two participant count"
            )

        upper_rounds = self._playoff_rounds(len(participants))
        lower_rounds = max(1, 2 * upper_rounds - 2)
        state = self._new_playoff_state(
            tournament_format="double_elimination",
            rounds=upper_rounds,
            lower_rounds=lower_rounds,
        )

        midpoint = len(participants) // 2
        first_half = participants[:midpoint]
        second_half = list(reversed(participants[midpoint:]))

        for position, (home, away) in enumerate(
            zip(first_half, second_half),
            start=1,
        ):
            match = self.match_repository.create(
                tournament_id=tournament.id,
                home_team_id=home.team_id,
                away_team_id=away.team_id,
                status=MatchStatus.SCHEDULED,
                scheduled_at=None,
                stage=DOUBLE_UPPER_STAGE,
                round_number=1,
                bracket_position=position,
            )
            self._register_playoff_advancement(
                state,
                match,
                tournament_format="double_elimination",
                rounds=upper_rounds,
                lower_rounds=lower_rounds,
            )

        self._save_bracket_state(tournament, state)

    def _generate_round_robin_matches(
        self,
        *,
        tournament: Tournament,
        participants: list[TournamentParticipant],
    ) -> None:
        team_ids = [participant.team_id for participant in participants]

        for round_number, round_pairs in enumerate(
            self._build_round_robin_pairs(team_ids),
            start=1,
        ):
            for position, (home_team_id, away_team_id) in enumerate(
                round_pairs,
                start=1,
            ):
                self.match_repository.create(
                    tournament_id=tournament.id,
                    home_team_id=home_team_id,
                    away_team_id=away_team_id,
                    status=MatchStatus.SCHEDULED,
                    scheduled_at=None,
                    stage=ROUND_ROBIN_STAGE,
                    round_number=round_number,
                    bracket_position=position,
                )

        state = {
            "format": "round_robin",
            "team_ids": team_ids,
            "generated_at": datetime.now(UTC).isoformat(),
        }
        self._save_bracket_state(tournament, state)

    def _generate_swiss_matches(
        self,
        *,
        tournament: Tournament,
        participants: list[TournamentParticipant],
    ) -> None:
        if len(participants) % 2 != 0:
            raise TournamentBracketNotReadyError(
                "Swiss bracket requires an even number of approved participants"
            )

        team_ids = [participant.team_id for participant in participants]
        settings = tournament.bracket_settings or {}
        max_rounds = int(settings.get("rounds") or max(1, ceil(log2(len(team_ids)))))

        for position, (home_team_id, away_team_id) in enumerate(
            self._pair_adjacent_teams(team_ids),
            start=1,
        ):
            self.match_repository.create(
                tournament_id=tournament.id,
                home_team_id=home_team_id,
                away_team_id=away_team_id,
                status=MatchStatus.SCHEDULED,
                scheduled_at=None,
                stage=SWISS_STAGE,
                round_number=1,
                bracket_position=position,
            )

        state = {
            "format": "swiss",
            "team_ids": team_ids,
            "current_round": 1,
            "max_rounds": max_rounds,
            "generated_at": datetime.now(UTC).isoformat(),
        }
        self._save_bracket_state(tournament, state)

    @staticmethod
    def _ensure_owner_access(tournament: Tournament, acting_user_id: int) -> None:
        if tournament.owner_id != acting_user_id:
            raise TournamentAccessDeniedError(
                "Only tournament owner can perform this action"
            )

    @staticmethod
    def _normalize_format(value: str) -> str:
        return value.strip().lower().replace("-", "_").replace(" ", "_")

    @staticmethod
    def _is_power_of_two(value: int) -> bool:
        return value > 0 and value & (value - 1) == 0

    @staticmethod
    def _playoff_rounds(participant_count: int) -> int:
        return int(log2(participant_count))

    @staticmethod
    def _sort_participants_for_bracket(
        tournament: Tournament,
        participants: list[TournamentParticipant],
    ) -> list[TournamentParticipant]:
        settings = tournament.bracket_settings or {}
        seed_policy = str(
            settings.get("seed_policy") or settings.get("seeding") or ""
        ).lower()

        if seed_policy in {"rating", "rating_desc", "elo"}:
            return sorted(
                participants,
                key=lambda participant: (
                    -(participant.team.owner.rating if participant.team else 1000),
                    participant.id,
                ),
            )

        return sorted(participants, key=lambda participant: participant.id)

    def _save_bracket_state(self, tournament: Tournament, state: dict) -> None:
        settings = dict(tournament.bracket_settings or {})
        settings[BRACKET_STATE_KEY] = state
        self.repository.update_bracket_settings(tournament, settings)

    @staticmethod
    def _new_playoff_state(
        *,
        tournament_format: str,
        rounds: int,
        lower_rounds: int | None = None,
    ) -> dict:
        state = {
            "format": tournament_format,
            "rounds": rounds,
            "slots": {},
            "created_targets": {},
            "advancements": {},
            "generated_at": datetime.now(UTC).isoformat(),
        }
        if lower_rounds is not None:
            state["lower_rounds"] = lower_rounds
        return state

    def _register_playoff_advancement(
        self,
        state: dict,
        match: Match,
        *,
        tournament_format: str,
        rounds: int,
        lower_rounds: int | None = None,
    ) -> None:
        advancement: dict[str, dict | None] = {"winner": None, "loser": None}

        if tournament_format == "single_elimination":
            advancement["winner"] = self._single_winner_target(match, rounds)
        elif tournament_format == "double_elimination":
            advancement["winner"] = self._double_winner_target(
                match,
                rounds,
                lower_rounds or 1,
            )
            advancement["loser"] = self._double_loser_target(
                match,
                rounds,
            )

        state["advancements"][str(match.id)] = advancement

    @staticmethod
    def _single_winner_target(match: Match, rounds: int) -> dict | None:
        if match.round_number >= rounds:
            return None

        return {
            "stage": MAIN_BRACKET_STAGE,
            "round_number": match.round_number + 1,
            "bracket_position": (match.bracket_position + 1) // 2,
            "slot": "home" if match.bracket_position % 2 == 1 else "away",
        }

    @staticmethod
    def _double_winner_target(
        match: Match,
        upper_rounds: int,
        lower_rounds: int,
    ) -> dict | None:
        if match.stage == DOUBLE_UPPER_STAGE:
            if match.round_number < upper_rounds:
                return {
                    "stage": DOUBLE_UPPER_STAGE,
                    "round_number": match.round_number + 1,
                    "bracket_position": (match.bracket_position + 1) // 2,
                    "slot": "home" if match.bracket_position % 2 == 1 else "away",
                }

            return {
                "stage": DOUBLE_GRAND_FINAL_STAGE,
                "round_number": 1,
                "bracket_position": 1,
                "slot": "home",
            }

        if match.stage == DOUBLE_LOWER_STAGE:
            if match.round_number >= lower_rounds:
                return {
                    "stage": DOUBLE_GRAND_FINAL_STAGE,
                    "round_number": 1,
                    "bracket_position": 1,
                    "slot": "away",
                }

            if match.round_number % 2 == 1:
                return {
                    "stage": DOUBLE_LOWER_STAGE,
                    "round_number": match.round_number + 1,
                    "bracket_position": match.bracket_position,
                    "slot": "home",
                }

            return {
                "stage": DOUBLE_LOWER_STAGE,
                "round_number": match.round_number + 1,
                "bracket_position": (match.bracket_position + 1) // 2,
                "slot": "home" if match.bracket_position % 2 == 1 else "away",
            }

        return None

    @staticmethod
    def _double_loser_target(match: Match, upper_rounds: int) -> dict | None:
        if match.stage != DOUBLE_UPPER_STAGE:
            return None

        if match.round_number == 1:
            return {
                "stage": DOUBLE_LOWER_STAGE,
                "round_number": 1,
                "bracket_position": (match.bracket_position + 1) // 2,
                "slot": "home" if match.bracket_position % 2 == 1 else "away",
            }

        if match.round_number <= upper_rounds:
            return {
                "stage": DOUBLE_LOWER_STAGE,
                "round_number": 2 * match.round_number - 2,
                "bracket_position": match.bracket_position,
                "slot": "away",
            }

        return None

    @staticmethod
    def _build_round_robin_pairs(team_ids: list[int]) -> list[list[tuple[int, int]]]:
        rotating: list[int | None] = list(team_ids)
        if len(rotating) % 2 == 1:
            rotating.append(None)

        rounds: list[list[tuple[int, int]]] = []
        for _ in range(len(rotating) - 1):
            pairs: list[tuple[int, int]] = []
            for index in range(len(rotating) // 2):
                home_team_id = rotating[index]
                away_team_id = rotating[-index - 1]
                if home_team_id is not None and away_team_id is not None:
                    pairs.append((home_team_id, away_team_id))

            rounds.append(pairs)
            rotating = [rotating[0], rotating[-1], *rotating[1:-1]]

        return rounds

    @staticmethod
    def _pair_adjacent_teams(team_ids: list[int]) -> list[tuple[int, int]]:
        return [
            (team_ids[index], team_ids[index + 1])
            for index in range(0, len(team_ids), 2)
        ]
