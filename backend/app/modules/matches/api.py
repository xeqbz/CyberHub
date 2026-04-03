from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_active_user
from app.modules.matches.repository import MatchRepository
from app.modules.matches.schemas import (
    MatchCreate,
    MatchListItem,
    MatchRead,
    MatchScoreUpdate,
    MatchUpdate,
)
from app.modules.matches.service import (
    MatchAccessDeniedError,
    MatchInvalidScoreError,
    MatchInvalidWinnerError,
    MatchNotFoundError,
    MatchService,
    MatchTeamNotFoundError,
    MatchTeamNotInTournamentError,
    MatchTeamsMustBeDifferentError,
    MatchTournamentNotFoundError,
)
from app.modules.teams.repository import TeamRepository
from app.modules.tournaments.repository import TournamentRepository
from app.modules.users.model import User

router = APIRouter(prefix="/matches", tags=["matches"])


def get_match_service(db: Session) -> MatchService:
    match_repository = MatchRepository(db)
    tournament_repository = TournamentRepository(db)
    team_repository = TeamRepository(db)
    return MatchService(
        repository=match_repository,
        tournament_repository=tournament_repository,
        team_repository=team_repository,
    )


@router.post(
    "",
    response_model=MatchRead,
    status_code=status.HTTP_201_CREATED,
)
def create_match(
    payload: MatchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> MatchRead:
    service = get_match_service(db)

    try:
        match = service.create_match(payload, acting_user_id=current_user.id)
    except MatchTournamentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tournament not found",
        ) from exc
    except MatchAccessDeniedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only tournament owner can perform this action",
        ) from exc
    except MatchTeamNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except MatchTeamsMustBeDifferentError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="home_team_id and away_team_id must be different",
        ) from exc
    except MatchTeamNotInTournamentError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Team is not registered in this tournament",
        ) from exc

    return match


@router.get(
    "",
    response_model=list[MatchListItem],
    status_code=status.HTTP_200_OK,
)
def list_matches(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[MatchListItem]:
    service = get_match_service(db)
    return service.list_matches(offset=offset, limit=limit)


@router.get(
    "/{match_id}",
    response_model=MatchRead,
    status_code=status.HTTP_200_OK,
)
def get_match(
    match_id: int,
    db: Session = Depends(get_db),
) -> MatchRead:
    service = get_match_service(db)

    match = service.get_match_by_id(match_id)
    if match is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found",
        )

    return match


@router.get(
    "/tournament/{tournament_id}",
    response_model=list[MatchRead],
    status_code=status.HTTP_200_OK,
)
def list_tournament_matches(
    tournament_id: int,
    db: Session = Depends(get_db),
) -> list[MatchRead]:
    service = get_match_service(db)

    try:
        return service.list_tournament_matches(tournament_id)
    except MatchTournamentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tournament not found",
        ) from exc


@router.patch(
    "/{match_id}",
    response_model=MatchRead,
    status_code=status.HTTP_200_OK,
)
def update_match(
    match_id: int,
    payload: MatchUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> MatchRead:
    service = get_match_service(db)

    try:
        match = service.update_match(
            match_id=match_id,
            acting_user_id=current_user.id,
            data=payload,
        )
    except MatchNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found",
        ) from exc
    except MatchTournamentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tournament not found",
        ) from exc
    except MatchAccessDeniedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only tournament owner can perform this action",
        ) from exc
    except MatchInvalidWinnerError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except MatchInvalidScoreError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return match


@router.patch(
    "/{match_id}/score",
    response_model=MatchRead,
    status_code=status.HTTP_200_OK,
)
def update_match_score(
    match_id: int,
    payload: MatchScoreUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> MatchRead:
    service = get_match_service(db)

    try:
        match = service.update_match_score(
            match_id=match_id,
            acting_user_id=current_user.id,
            data=payload,
        )
    except MatchNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found",
        ) from exc
    except MatchTournamentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tournament not found",
        ) from exc
    except MatchAccessDeniedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only tournament owner can perform this action",
        ) from exc
    except MatchInvalidWinnerError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return match


@router.delete(
    "/{match_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_match(
    match_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Response:
    service = get_match_service(db)

    try:
        service.delete_match(
            match_id=match_id,
            acting_user_id=current_user.id,
        )
    except MatchNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found",
        ) from exc
    except MatchTournamentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tournament not found",
        ) from exc
    except MatchAccessDeniedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only tournament owner can perform this action",
        ) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)