from fastapi import Depends, FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.api.health import router as health_router
from app.api.router import api_router
from app.core.config import settings
from app.db.session import get_db
from app.modules.platform.realtime import stream_notifications

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.websocket("/ws/notifications")
async def websocket_notifications(
    websocket: WebSocket,
    db: Session = Depends(get_db),
) -> None:
    await stream_notifications(websocket, db)
