from fastapi import APIRouter, Depends, status

from app.modules.auth.dependencies import get_current_active_user
from app.modules.users.model import User
from app.modules.users.schemas import UserRead

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/me",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
)
def read_current_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    return current_user