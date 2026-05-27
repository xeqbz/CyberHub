from copy import deepcopy
from datetime import UTC, datetime

from app.modules.matches.model import Match, MatchStatus
from app.modules.matches.repository import MatchRepository
from app.modules.matches.schemas import MatchCreate, MatchScoreUpdate, MatchUpdate
from app.modules.teams.repository import TeamRepository
from app.modules.tournaments.model import Tournament, TournamentParticipantStatus
from app.modules.tournaments.repository import TournamentRepository


BRACKET_STATE_KEY = "_cyberhub_bracket"
DOUBLE_UPPER_STAGE = "Upper bracket"
DOUBLE_LOWER_STAGE = "Lower bracket"
DOUBLE_GRAND_FINAL_STAGE = "Grand final"
MAIN_BRACKET_STAGE = "Main bracket"
SWISS_STAGE = "Swiss"


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
        self._validate_team_registered_in_tournament(
            data.tournament_id, data.home_team_id
        )
        self._validate_team_registered_in_tournament(
            data.tournament_id, data.away_team_id
        )

        match = self.repository.create(
            tournament_id=data.tournament_id,
            home_team_id=data.home_team_id,
            away_team_id=data.away_team_id,
            status=MatchStatus.SCHEDULED,
            scheduled_at=data.scheduled_at,
            stage=data.stage.strip(),
            round_number=data.round_number,
            bracket_position=data.bracket_position,
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
        was_completed = match.status == MatchStatus.COMPLETED

        winner_team_id = (
            match.winner_team_id if data.winner_team_id is None else data.winner_team_id
        )
        status = data.status

        home_score = match.home_score if data.home_score is None else data.home_score
        away_score = match.away_score if data.away_score is None else data.away_score

        scores_were_provided = (
            data.home_score is not None or data.away_score is not None
        )
        if (data.home_score is None) != (data.away_score is None):
            raise MatchInvalidScoreError(
                "Both home_score and away_score must be provided together"
            )

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

        if status == MatchStatus.COMPLETED and (
            home_score is None or away_score is None
        ):
            raise MatchInvalidScoreError("Completed match must have both scores")

        completed_at_was_provided = False
        completed_at = None
        result_confirmed_by_id = None
        if status == MatchStatus.COMPLETED:
            completed_at_was_provided = True
            completed_at = datetime.now(UTC)
            result_confirmed_by_id = acting_user_id

        updated_match = self.repository.update(
            match,
            status=status,
            scheduled_at=data.scheduled_at,
            stage=data.stage.strip() if data.stage is not None else None,
            round_number=data.round_number,
            bracket_position=data.bracket_position,
            home_score=data.home_score,
            away_score=data.away_score,
            winner_team_id=winner_team_id,
            result_confirmed_by_id=result_confirmed_by_id,
            completed_at=completed_at,
            completed_at_was_provided=completed_at_was_provided,
        )

        if status == MatchStatus.COMPLETED and not was_completed:
            self._advance_bracket_after_completion(updated_match, tournament)

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
        was_completed = match.status == MatchStatus.COMPLETED

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
            result_confirmed_by_id=acting_user_id,
            completed_at=datetime.now(UTC),
            completed_at_was_provided=True,
        )

        if not was_completed:
            self._advance_bracket_after_completion(updated_match, tournament)

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
            raise MatchTeamsMustBeDifferentError(
                "home_team_id and away_team_id must be different"
            )

    def _validate_team_registered_in_tournament(
        self, tournament_id: int, team_id: int
    ) -> None:
        participant = self.tournament_repository.get_participant(
            tournament_id=tournament_id,
            team_id=team_id,
        )
        if (
            participant is None
            or participant.status != TournamentParticipantStatus.APPROVED
        ):
            raise MatchTeamNotInTournamentError(
                "Team is not registered in this tournament"
            )

    @staticmethod
    def _ensure_tournament_owner_access(
        tournament: Tournament, acting_user_id: int
    ) -> None:
        if tournament.owner_id != acting_user_id:
            raise MatchAccessDeniedError(
                "Only tournament owner can perform this action"
            )

    @staticmethod
    def _resolve_winner_team_id(
        *,
        home_team_id: int,
        away_team_id: int,
        home_score: int,
        away_score: int,
        winner_team_id: int | None,
    ) -> int | None:
        if winner_team_id is not None and winner_team_id not in {
            home_team_id,
            away_team_id,
        }:
            raise MatchInvalidWinnerError(
                "winner_team_id must match one of the match teams"
            )

        if home_score > away_score:
            expected_winner = home_team_id
        elif away_score > home_score:
            expected_winner = away_team_id
        else:
            expected_winner = None

        if winner_team_id is None:
            return expected_winner

        if winner_team_id != expected_winner:
            raise MatchInvalidWinnerError(
                "winner_team_id does not match the provided score"
            )

        return winner_team_id

    def _advance_bracket_after_completion(
        self,
        match: Match,
        tournament: Tournament,
    ) -> None:
        state = self._get_bracket_state(tournament)
        if not state:
            return

        if state.get("format") == "swiss" and match.stage == SWISS_STAGE:
            self._advance_swiss_if_round_complete(tournament, state)
            self._save_bracket_state(tournament, state)
            return

        if match.winner_team_id is None:
            return

        advancement = state.get("advancements", {}).get(str(match.id))
        if not advancement:
            return

        winner_target = advancement.get("winner")
        if winner_target is not None:
            self._advance_team_to_target(
                tournament,
                state,
                winner_target,
                match.winner_team_id,
            )

        loser_target = advancement.get("loser")
        loser_team_id = self._get_loser_team_id(match)
        if loser_target is not None and loser_team_id is not None:
            self._advance_team_to_target(
                tournament,
                state,
                loser_target,
                loser_team_id,
            )

        self._save_bracket_state(tournament, state)

    @staticmethod
    def _get_loser_team_id(match: Match) -> int | None:
        if match.winner_team_id == match.home_team_id:
            return match.away_team_id
        if match.winner_team_id == match.away_team_id:
            return match.home_team_id
        return None

    @staticmethod
    def _get_bracket_state(tournament: Tournament) -> dict | None:
        settings = tournament.bracket_settings or {}
        state = settings.get(BRACKET_STATE_KEY)
        return deepcopy(state) if isinstance(state, dict) else None

    def _save_bracket_state(self, tournament: Tournament, state: dict) -> None:
        settings = dict(tournament.bracket_settings or {})
        settings[BRACKET_STATE_KEY] = state
        self.tournament_repository.update_bracket_settings(tournament, settings)

    def _advance_team_to_target(
        self,
        tournament: Tournament,
        state: dict,
        target: dict,
        team_id: int,
    ) -> None:
        key = self._target_key(target)
        slots = state.setdefault("slots", {})
        slot_data = slots.setdefault(key, {})
        slot_name = target["slot"]

        existing_team_id = slot_data.get(slot_name)
        if existing_team_id is not None:
            return

        slot_data[slot_name] = team_id
        home_team_id = slot_data.get("home")
        away_team_id = slot_data.get("away")
        created_targets = state.setdefault("created_targets", {})

        if not home_team_id or not away_team_id or key in created_targets:
            return

        created_match = self.repository.create(
            tournament_id=tournament.id,
            home_team_id=home_team_id,
            away_team_id=away_team_id,
            status=MatchStatus.SCHEDULED,
            scheduled_at=None,
            stage=target["stage"],
            round_number=int(target["round_number"]),
            bracket_position=int(target["bracket_position"]),
        )
        created_targets[key] = created_match.id
        self._register_created_match_advancement(state, created_match)

    @staticmethod
    def _target_key(target: dict) -> str:
        return (
            f"{target['stage']}|{target['round_number']}|"
            f"{target['bracket_position']}"
        )

    def _register_created_match_advancement(self, state: dict, match: Match) -> None:
        tournament_format = state.get("format")
        advancement: dict[str, dict | None] = {"winner": None, "loser": None}

        if tournament_format == "single_elimination":
            advancement["winner"] = self._single_winner_target(
                match,
                int(state.get("rounds", 1)),
            )
        elif tournament_format == "double_elimination":
            advancement["winner"] = self._double_winner_target(
                match,
                int(state.get("rounds", 1)),
                int(state.get("lower_rounds", 1)),
            )
            advancement["loser"] = self._double_loser_target(
                match,
                int(state.get("rounds", 1)),
            )

        state.setdefault("advancements", {})[str(match.id)] = advancement

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

    def _advance_swiss_if_round_complete(
        self,
        tournament: Tournament,
        state: dict,
    ) -> None:
        current_round = int(state.get("current_round", 1))
        max_rounds = int(state.get("max_rounds", 1))
        if current_round >= max_rounds:
            return

        matches = [
            item
            for item in self.repository.list_by_tournament(tournament.id)
            if item.stage == SWISS_STAGE
        ]
        current_round_matches = [
            item for item in matches if item.round_number == current_round
        ]
        if not current_round_matches or any(
            item.status != MatchStatus.COMPLETED for item in current_round_matches
        ):
            return

        next_round = current_round + 1
        if any(item.round_number == next_round for item in matches):
            state["current_round"] = next_round
            return

        standings = {team_id: 0 for team_id in state.get("team_ids", [])}
        played_pairs: set[tuple[int, int]] = set()
        for item in matches:
            played_pairs.add(tuple(sorted((item.home_team_id, item.away_team_id))))
            if item.status == MatchStatus.COMPLETED and item.winner_team_id is not None:
                standings[item.winner_team_id] = standings.get(
                    item.winner_team_id,
                    0,
                ) + 1

        ordered_team_ids = sorted(
            state.get("team_ids", []),
            key=lambda team_id: (-standings.get(team_id, 0), team_id),
        )
        pairs = self._build_swiss_pairs(ordered_team_ids, played_pairs)
        for position, (home_team_id, away_team_id) in enumerate(pairs, start=1):
            self.repository.create(
                tournament_id=tournament.id,
                home_team_id=home_team_id,
                away_team_id=away_team_id,
                status=MatchStatus.SCHEDULED,
                scheduled_at=None,
                stage=SWISS_STAGE,
                round_number=next_round,
                bracket_position=position,
            )

        state["current_round"] = next_round

    @staticmethod
    def _build_swiss_pairs(
        ordered_team_ids: list[int],
        played_pairs: set[tuple[int, int]],
    ) -> list[tuple[int, int]]:
        available = list(ordered_team_ids)
        pairs: list[tuple[int, int]] = []

        while len(available) >= 2:
            home_team_id = available.pop(0)
            opponent_index = 0

            for index, candidate_team_id in enumerate(available):
                pair = tuple(sorted((home_team_id, candidate_team_id)))
                if pair not in played_pairs:
                    opponent_index = index
                    break

            away_team_id = available.pop(opponent_index)
            pairs.append((home_team_id, away_team_id))

        return pairs
