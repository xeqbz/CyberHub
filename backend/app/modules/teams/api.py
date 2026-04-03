from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_active_user
from app.modules.teams.model import TeamMemberRole
from app.modules.teams.repository import TeamRepository
from app.modules.teams.schemas import (
    TeamCreate,
    TeamListItem,
    TeamMemberRead,
    TeamRead,
    TeamUpdate,
)
from app.modules.teams.service import (
    TeamAccessDeniedError,
    TeamAlreadyExistsError,
    TeamMemberAlreadyExistsError,
    TeamMemberNotFoundError,
    TeamNotFoundError,
    TeamOwnerRemovalError,
    TeamOwnerRoleChangeError,
    TeamService,
)
from app.modules.users.model import User

router = APIRouter(prefix="/teams", tags=["teams"])


class TeamMemberCreateRequest(BaseModel):
    user_id: int
    role: TeamMemberRole = TeamMemberRole.MEMBER


class TeamMemberRoleUpdateRequest(BaseModel):
    role: TeamMemberRole


def get_team_service(db: Session) -> TeamService:
    repository = TeamRepository(db)
    return TeamService(repository)


@router.post(
    "",
    response_model=TeamRead,
    status_code=status.HTTP_201_CREATED,
)
def create_team(
    payload: TeamCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TeamRead:
    service = get_team_service(db)

    try:
        team = service.create_team(payload, owner_id=current_user.id)
    except TeamAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Team with this name already exists",
        ) from exc

    return team


@router.get(
    "",
    response_model=list[TeamListItem],
    status_code=status.HTTP_200_OK,
)
def list_teams(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[TeamListItem]:
    service = get_team_service(db)
    return service.list_teams(offset=offset, limit=limit)


@router.get(
    "/my",
    response_model=list[TeamRead],
    status_code=status.HTTP_200_OK,
)
def list_my_teams(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[TeamRead]:
    service = get_team_service(db)
    return service.list_user_teams(current_user.id)


@router.get(
    "/{team_id}",
    response_model=TeamRead,
    status_code=status.HTTP_200_OK,
)
def get_team(
    team_id: int,
    db: Session = Depends(get_db),
) -> TeamRead:
    service = get_team_service(db)

    team = service.get_team_by_id(team_id)
    if team is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        )

    return team


@router.patch(
    "/{team_id}",
    response_model=TeamRead,
    status_code=status.HTTP_200_OK,
)
def update_team(
    team_id: int,
    payload: TeamUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TeamRead:
    service = get_team_service(db)

    try:
        team = service.update_team(
            team_id=team_id,
            acting_user_id=current_user.id,
            data=payload,
        )
    except TeamNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        ) from exc
    except TeamAccessDeniedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only team owner can perform this action",
        ) from exc
    except TeamAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Team with this name already exists",
        ) from exc

    return team


@router.delete(
    "/{team_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_team(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Response:
    service = get_team_service(db)

    try:
        service.delete_team(
            team_id=team_id,
            acting_user_id=current_user.id,
        )
    except TeamNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        ) from exc
    except TeamAccessDeniedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only team owner can perform this action",
        ) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{team_id}/members",
    response_model=list[TeamMemberRead],
    status_code=status.HTTP_200_OK,
)
def list_team_members(
    team_id: int,
    db: Session = Depends(get_db),
) -> list[TeamMemberRead]:
    service = get_team_service(db)

    try:
        return service.list_members(team_id)
    except TeamNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        ) from exc


@router.post(
    "/{team_id}/members",
    response_model=TeamMemberRead,
    status_code=status.HTTP_201_CREATED,
)
def add_team_member(
    team_id: int,
    payload: TeamMemberCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TeamMemberRead:
    service = get_team_service(db)

    try:
        return service.add_member(
            team_id=team_id,
            acting_user_id=current_user.id,
            user_id=payload.user_id,
            role=payload.role,
        )
    except TeamNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        ) from exc
    except TeamAccessDeniedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only team owner can perform this action",
        ) from exc
    except TeamMemberAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already a team member",
        ) from exc


@router.patch(
    "/{team_id}/members/{user_id}",
    response_model=TeamMemberRead,
    status_code=status.HTTP_200_OK,
)
def update_team_member_role(
    team_id: int,
    user_id: int,
    payload: TeamMemberRoleUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TeamMemberRead:
    service = get_team_service(db)

    try:
        return service.update_member_role(
            team_id=team_id,
            acting_user_id=current_user.id,
            user_id=user_id,
            role=payload.role,
        )
    except TeamNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        ) from exc
    except TeamAccessDeniedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only team owner can perform this action",
        ) from exc
    except TeamMemberNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team member not found",
        ) from exc
    except TeamOwnerRoleChangeError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Team owner role cannot be changed",
        ) from exc


@router.delete(
    "/{team_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_team_member(
    team_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Response:
    service = get_team_service(db)

    try:
        service.remove_member(
            team_id=team_id,
            acting_user_id=current_user.id,
            user_id=user_id,
        )
    except TeamNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        ) from exc
    except TeamAccessDeniedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only team owner can perform this action",
        ) from exc
    except TeamMemberNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team member not found",
        ) from exc
    except TeamOwnerRemovalError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Team owner cannot be removed",
        ) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)
