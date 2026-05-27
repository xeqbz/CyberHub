from collections.abc import Sequence

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.modules.tournaments.model import (
    Tournament,
    TournamentParticipant,
    TournamentParticipantStatus,
    TournamentStatus,
)


class TournamentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, tournament_id: int) -> Tournament | None:
        stmt = (
            select(Tournament)
            .where(Tournament.id == tournament_id)
            .options(
                joinedload(Tournament.owner),
                selectinload(Tournament.participants).joinedload(
                    TournamentParticipant.team
                ),
            )
        )
        return self.db.scalar(stmt)

    def get_by_name(self, name: str) -> Tournament | None:
        stmt = select(Tournament).where(Tournament.name == name)
        return self.db.scalar(stmt)

    def list_tournaments(
        self,
        offset: int = 0,
        limit: int = 100,
        *,
        search: str | None = None,
        statuses: Sequence[TournamentStatus] | None = None,
        discipline: str | None = None,
        format: str | None = None,
        owner_id: int | None = None,
    ) -> list[Tournament]:
        stmt = (
            select(Tournament)
            .options(joinedload(Tournament.owner))
        )

        if search:
            pattern = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    Tournament.name.ilike(pattern),
                    Tournament.description.ilike(pattern),
                    Tournament.discipline.ilike(pattern),
                    Tournament.format.ilike(pattern),
                )
            )

        if statuses:
            stmt = stmt.where(Tournament.status.in_(statuses))

        if discipline:
            stmt = stmt.where(Tournament.discipline.ilike(f"%{discipline.strip()}%"))

        if format:
            stmt = stmt.where(Tournament.format == format.strip())

        if owner_id is not None:
            stmt = stmt.where(Tournament.owner_id == owner_id)

        stmt = stmt.order_by(Tournament.created_at.desc(), Tournament.id.desc())
        stmt = stmt.offset(offset).limit(limit)
        return list(self.db.scalars(stmt).unique().all())

    def list_by_owner(self, owner_id: int) -> list[Tournament]:
        stmt = (
            select(Tournament)
            .where(Tournament.owner_id == owner_id)
            .options(
                joinedload(Tournament.owner),
                selectinload(Tournament.participants).joinedload(
                    TournamentParticipant.team
                ),
            )
            .order_by(Tournament.id)
        )
        return list(self.db.scalars(stmt).unique().all())

    def create(
        self,
        *,
        name: str,
        description: str | None,
        status,
        owner_id: int,
        format: str,
        discipline: str,
        rules: str,
        bracket_settings: dict | None,
        max_teams: int,
        starts_at,
    ) -> Tournament:
        tournament = Tournament(
            name=name,
            description=description,
            status=status,
            owner_id=owner_id,
            format=format,
            discipline=discipline,
            rules=rules,
            bracket_settings=bracket_settings,
            max_teams=max_teams,
            starts_at=starts_at,
        )
        self.db.add(tournament)
        self.db.commit()
        self.db.refresh(tournament)
        return tournament

    def update(
        self,
        tournament: Tournament,
        *,
        name: str | None = None,
        description: str | None = None,
        format: str | None = None,
        discipline: str | None = None,
        rules: str | None = None,
        bracket_settings: dict | None = None,
        bracket_settings_was_provided: bool = False,
        status=None,
        max_teams: int | None = None,
        starts_at=None,
    ) -> Tournament:
        if name is not None:
            tournament.name = name
        if description is not None:
            tournament.description = description
        if format is not None:
            tournament.format = format
        if discipline is not None:
            tournament.discipline = discipline
        if rules is not None:
            tournament.rules = rules
        if bracket_settings_was_provided:
            tournament.bracket_settings = bracket_settings
        if status is not None:
            tournament.status = status
        if max_teams is not None:
            tournament.max_teams = max_teams
        if starts_at is not None:
            tournament.starts_at = starts_at

        self.db.add(tournament)
        self.db.commit()
        self.db.refresh(tournament)
        return tournament

    def delete(self, tournament: Tournament) -> None:
        self.db.delete(tournament)
        self.db.commit()

    def update_bracket_settings(
        self,
        tournament: Tournament,
        bracket_settings: dict | None,
    ) -> Tournament:
        tournament.bracket_settings = bracket_settings
        self.db.add(tournament)
        self.db.commit()
        self.db.refresh(tournament)
        return tournament

    def get_participant(
        self, tournament_id: int, team_id: int
    ) -> TournamentParticipant | None:
        stmt = (
            select(TournamentParticipant)
            .where(
                TournamentParticipant.tournament_id == tournament_id,
                TournamentParticipant.team_id == team_id,
            )
            .options(joinedload(TournamentParticipant.team))
        )
        return self.db.scalar(stmt)

    def list_participants(self, tournament_id: int) -> list[TournamentParticipant]:
        stmt = (
            select(TournamentParticipant)
            .where(TournamentParticipant.tournament_id == tournament_id)
            .options(joinedload(TournamentParticipant.team))
            .order_by(TournamentParticipant.id)
        )
        return list(self.db.scalars(stmt).all())

    def count_participants(self, tournament_id: int) -> int:
        stmt = select(TournamentParticipant).where(
            TournamentParticipant.tournament_id == tournament_id,
            TournamentParticipant.status == TournamentParticipantStatus.APPROVED,
        )
        return len(list(self.db.scalars(stmt).all()))

    def add_participant(
        self,
        *,
        tournament_id: int,
        team_id: int,
        status: TournamentParticipantStatus,
        decided_by_id: int | None = None,
        decided_at=None,
    ) -> TournamentParticipant:
        participant = TournamentParticipant(
            tournament_id=tournament_id,
            team_id=team_id,
            status=status,
            decided_by_id=decided_by_id,
            decided_at=decided_at,
        )
        self.db.add(participant)
        self.db.commit()
        self.db.refresh(participant)
        return participant

    def update_participant(
        self,
        participant: TournamentParticipant,
        *,
        status: TournamentParticipantStatus,
        decided_by_id: int,
        decided_at,
    ) -> TournamentParticipant:
        participant.status = status
        participant.decided_by_id = decided_by_id
        participant.decided_at = decided_at

        self.db.add(participant)
        self.db.commit()
        self.db.refresh(participant)
        return participant

    def remove_participant(self, participant: TournamentParticipant) -> None:
        self.db.delete(participant)
        self.db.commit()
