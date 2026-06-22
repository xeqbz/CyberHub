from fastapi import APIRouter

from app.modules.auth.api import router as auth_router
from app.modules.matches.api import router as matches_router
from app.modules.platform.api import router as platform_router
from app.modules.teams.api import router as teams_router
from app.modules.tournaments.api import router as tournaments_router
from app.modules.users.api import router as users_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(teams_router)
api_router.include_router(tournaments_router)
api_router.include_router(matches_router)
api_router.include_router(platform_router)
