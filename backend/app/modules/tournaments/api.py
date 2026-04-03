from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_active_user
from app.modules.teams.repository import TeamRepository
from app.modules.tournaments.repository import TournamentRepository
from app.modules.tournaments.schemas import (
    TournamentCreate,
    TournamentListItem,
    TournamentParticipantCreate,
    TournamentParticipantRead,
    TournamentRead,
    TournamentUpdate,
)
from app.modules.tournaments.service import (
    TournamentAccessDeniedError,
    TournamentAlreadyExistsError,
    TournamentCapacityExceededError,
    TournamentNotFoundError,
    TournamentParticipantAlreadyExistsError,
    TournamentParticipantNotFoundError,
    TournamentRegistrationClosedError,
    TournamentService,
    TournamentTeamAccessDeniedError,
    TournamentTeamNotFoundError,
)
from app.modules.users.model import User

router = APIRouter(prefix="/tournaments", tags=["tournaments"])


def get_tournament_service(db: Session) -> TournamentService:
    tournament_repository = TournamentRepository(db)
    team_repository = TeamRepository(db)
    return TournamentService(tournament_repository, team_repository)


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

    return tournament


@router.get(
    "",
    response_model=list[TournamentListItem],
    status_code=status.HTTP_200_OK,
)
def list_tournaments(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[TournamentListItem]:
    service = get_tournament_service(db)
    return service.list_tournaments(offset=offset, limit=limit)


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
        return service.add_participant(
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
