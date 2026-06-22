from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_active_user
from app.modules.matches.repository import MatchRepository
from app.modules.matches.schemas import MatchRead
from app.modules.platform.service import create_notification, record_action
from app.modules.teams.repository import TeamRepository
from app.modules.tournaments.model import TournamentParticipantStatus, TournamentStatus
from app.modules.tournaments.repository import TournamentRepository
from app.modules.tournaments.schemas import (
    TournamentCreate,
    TournamentListItem,
    TournamentParticipantCreate,
    TournamentParticipantRead,
    TournamentParticipantReview,
    TournamentRead,
    TournamentUpdate,
)
from app.modules.tournaments.service import (
    TournamentAccessDeniedError,
    TournamentAlreadyExistsError,
    TournamentBracketAlreadyExistsError,
    TournamentBracketNotReadyError,
    TournamentCapacityExceededError,
    TournamentLockedError,
    TournamentNotFoundError,
    TournamentParticipantAlreadyExistsError,
    TournamentParticipantNotFoundError,
    TournamentRegistrationClosedError,
    TournamentService,
    TournamentTeamAccessDeniedError,
    TournamentTeamNotFoundError,
    TournamentUnsupportedFormatError,
)
from app.modules.users.model import User

router = APIRouter(prefix="/tournaments", tags=["tournaments"])


def get_tournament_service(db: Session) -> TournamentService:
    tournament_repository = TournamentRepository(db)
    team_repository = TeamRepository(db)
    match_repository = MatchRepository(db)
    return TournamentService(
        tournament_repository,
        team_repository,
        match_repository,
    )


@router.post(
    "",
    response_model=TournamentRead,
    status_code=status.HTTP_201_CREATED,
)
def create_tournament(
    payload: TournamentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TournamentRead:
    service = get_tournament_service(db)

    try:
        tournament = service.create_tournament(payload, owner_id=current_user.id)
    except TournamentAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Tournament with this name already exists",
        ) from exc

    record_action(
        db,
        actor_id=current_user.id,
        action="tournament_created",
        entity_type="tournament",
        entity_id=tournament.id,
        details={"name": tournament.name, "status": tournament.status},
    )
    return tournament


@router.get(
    "",
    response_model=list[TournamentListItem],
    status_code=status.HTTP_200_OK,
)
def list_tournaments(
    search: str | None = Query(default=None, max_length=120),
    status_filter: TournamentStatus | None = Query(default=None, alias="status"),
    scope: str | None = Query(
        default=None,
        pattern="^(ALL|MY_TOURNAMENTS|OPEN|ACTIVE|COMPLETED)$",
    ),
    discipline: str | None = Query(default=None, max_length=120),
    format: str | None = Query(default=None, max_length=80),
    owner_id: int | None = Query(default=None, ge=1),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[TournamentListItem]:
    service = get_tournament_service(db)
    statuses: list[TournamentStatus] | None = None

    if status_filter is not None:
        statuses = [status_filter]
    elif scope == "OPEN":
        statuses = [TournamentStatus.REGISTRATION_OPEN]
    elif scope == "ACTIVE":
        statuses = [
            TournamentStatus.REGISTRATION_OPEN,
            TournamentStatus.REGISTRATION_CLOSED,
            TournamentStatus.IN_PROGRESS,
        ]
    elif scope == "COMPLETED":
        statuses = [TournamentStatus.COMPLETED]

    return service.list_tournaments(
        offset=offset,
        limit=limit,
        search=search,
        statuses=statuses,
        discipline=discipline,
        format=format,
        owner_id=owner_id,
    )


@router.get(
    "/{tournament_id}",
    response_model=TournamentRead,
    status_code=status.HTTP_200_OK,
)
def get_tournament(
    tournament_id: int,
    db: Session = Depends(get_db),
) -> TournamentRead:
    service = get_tournament_service(db)

    tournament = service.get_tournament_by_id(tournament_id)
    if tournament is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tournament not found",
        )

    return tournament


@router.patch(
    "/{tournament_id}",
    response_model=TournamentRead,
    status_code=status.HTTP_200_OK,
)
def update_tournament(
    tournament_id: int,
    payload: TournamentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TournamentRead:
    service = get_tournament_service(db)
    previous_tournament = service.get_tournament_by_id(tournament_id)
    previous_status = previous_tournament.status if previous_tournament else None

    try:
        tournament = service.update_tournament(
            tournament_id=tournament_id,
            acting_user_id=current_user.id,
            data=payload,
        )
    except TournamentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tournament not found",
        ) from exc
    except TournamentAccessDeniedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only tournament owner can perform this action",
        ) from exc
    except TournamentAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Tournament with this name already exists",
        ) from exc
    except TournamentCapacityExceededError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except TournamentLockedError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    if payload.status is not None and payload.status != previous_status:
        create_notification(
            db,
            user_id=tournament.owner_id,
            title="Tournament status updated",
            message=(
                f"Tournament {tournament.name} status changed "
                f"to {tournament.status}."
            ),
            related_entity_type="tournament",
            related_entity_id=tournament.id,
        )

    record_action(
        db,
        actor_id=current_user.id,
        action="tournament_updated",
        entity_type="tournament",
        entity_id=tournament.id,
        details=payload.model_dump(exclude_unset=True, mode="json"),
    )
    return tournament


@router.delete(
    "/{tournament_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_tournament(
    tournament_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Response:
    service = get_tournament_service(db)

    try:
        service.delete_tournament(
            tournament_id=tournament_id,
            acting_user_id=current_user.id,
        )
    except TournamentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tournament not found",
        ) from exc
    except TournamentAccessDeniedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only tournament owner can perform this action",
        ) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{tournament_id}/bracket/generate",
    response_model=list[MatchRead],
    status_code=status.HTTP_201_CREATED,
)
def generate_tournament_bracket(
    tournament_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[MatchRead]:
    service = get_tournament_service(db)

    try:
        matches = service.generate_bracket(
            tournament_id=tournament_id,
            acting_user_id=current_user.id,
        )
    except TournamentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tournament not found",
        ) from exc
    except TournamentAccessDeniedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only tournament owner can perform this action",
        ) from exc
    except TournamentBracketAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except (
        TournamentBracketNotReadyError,
        TournamentUnsupportedFormatError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    notified_owner_ids: set[int] = set()
    for match in matches:
        for team in (match.home_team, match.away_team):
            if team.owner_id in notified_owner_ids:
                continue
            notified_owner_ids.add(team.owner_id)
            create_notification(
                db,
                user_id=team.owner_id,
                title="Tournament bracket generated",
                message=f"Bracket for {match.tournament.name} is ready.",
                related_entity_type="tournament",
                related_entity_id=match.tournament_id,
            )

    record_action(
        db,
        actor_id=current_user.id,
        action="tournament_bracket_generated",
        entity_type="tournament",
        entity_id=tournament_id,
        details={"matches_created": len(matches)},
    )
    return matches


@router.get(
    "/{tournament_id}/participants",
    response_model=list[TournamentParticipantRead],
    status_code=status.HTTP_200_OK,
)
def list_tournament_participants(
    tournament_id: int,
    db: Session = Depends(get_db),
) -> list[TournamentParticipantRead]:
    service = get_tournament_service(db)

    try:
        return service.list_participants(tournament_id)
    except TournamentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tournament not found",
        ) from exc


@router.post(
    "/{tournament_id}/participants",
    response_model=TournamentParticipantRead,
    status_code=status.HTTP_201_CREATED,
)
def add_tournament_participant(
    tournament_id: int,
    payload: TournamentParticipantCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TournamentParticipantRead:
    service = get_tournament_service(db)

    try:
        participant = service.add_participant(
            tournament_id=tournament_id,
            team_id=payload.team_id,
            acting_user_id=current_user.id,
        )
    except TournamentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tournament not found",
        ) from exc
    except TournamentRegistrationClosedError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Tournament registration is not open",
        ) from exc
    except TournamentTeamNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        ) from exc
    except TournamentTeamAccessDeniedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only team owner or tournament owner can register the team",
        ) from exc
    except TournamentParticipantAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Team is already registered in this tournament",
        ) from exc
    except TournamentCapacityExceededError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Tournament participant limit has been reached",
        ) from exc

    tournament = service.get_tournament_by_id(tournament_id)
    if tournament is not None:
        if participant.status == TournamentParticipantStatus.PENDING:
            create_notification(
                db,
                user_id=tournament.owner_id,
                title="New tournament application",
                message=f"Team {participant.team.name} applied to {tournament.name}.",
                related_entity_type="tournament",
                related_entity_id=tournament.id,
            )
        else:
            create_notification(
                db,
                user_id=participant.team.owner_id,
                title="Tournament registration approved",
                message=f"Team {participant.team.name} joined {tournament.name}.",
                related_entity_type="tournament",
                related_entity_id=tournament.id,
            )

    record_action(
        db,
        actor_id=current_user.id,
        action="tournament_participant_registered",
        entity_type="tournament_participant",
        entity_id=participant.id,
        details={"status": participant.status},
    )
    return participant


@router.delete(
    "/{tournament_id}/participants/{team_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_tournament_participant(
    tournament_id: int,
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Response:
    service = get_tournament_service(db)

    try:
        service.remove_participant(
            tournament_id=tournament_id,
            team_id=team_id,
            acting_user_id=current_user.id,
        )
    except TournamentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tournament not found",
        ) from exc
    except TournamentParticipantNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tournament participant not found",
        ) from exc
    except TournamentTeamNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        ) from exc
    except TournamentTeamAccessDeniedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only team owner or tournament owner can remove the team",
        ) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch(
    "/{tournament_id}/participants/{team_id}",
    response_model=TournamentParticipantRead,
    status_code=status.HTTP_200_OK,
)
def review_tournament_participant(
    tournament_id: int,
    team_id: int,
    payload: TournamentParticipantReview,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TournamentParticipantRead:
    service = get_tournament_service(db)

    try:
        participant = service.review_participant(
            tournament_id=tournament_id,
            team_id=team_id,
            acting_user_id=current_user.id,
            data=payload,
        )
    except TournamentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tournament not found",
        ) from exc
    except TournamentParticipantNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tournament participant not found",
        ) from exc
    except TournamentAccessDeniedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only tournament owner can perform this action",
        ) from exc
    except TournamentCapacityExceededError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Tournament participant limit has been reached",
        ) from exc

    tournament = service.get_tournament_by_id(tournament_id)
    if tournament is not None:
        create_notification(
            db,
            user_id=participant.team.owner_id,
            title="Tournament application reviewed",
            message=(
                f"Application for {participant.team.name} in {tournament.name} "
                f"was marked as {participant.status}."
            ),
            related_entity_type="tournament",
            related_entity_id=tournament.id,
        )

    record_action(
        db,
        actor_id=current_user.id,
        action="tournament_participant_reviewed",
        entity_type="tournament_participant",
        entity_id=participant.id,
        details={"status": participant.status},
    )
    return participant
