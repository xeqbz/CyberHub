import asyncio
from datetime import UTC, datetime
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.auth.security import get_subject_from_token
from app.modules.matches.model import Match, MatchStatus
from app.modules.platform.model import (
    DisputeStatus,
    MatchDispute,
    Notification,
    RankedMatch,
)
from app.modules.teams.model import Team
from app.modules.tournaments.model import Tournament
from app.modules.users.model import User

NOTIFICATION_POLL_INTERVAL_SECONDS = 3


def _iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.isoformat()


def _serialize_notification(notification: Notification) -> dict[str, Any]:
    return {
        "id": notification.id,
        "user_id": notification.user_id,
        "title": notification.title,
        "message": notification.message,
        "is_read": notification.is_read,
        "related_entity_type": notification.related_entity_type,
        "related_entity_id": notification.related_entity_id,
        "created_at": _iso(notification.created_at),
        "updated_at": _iso(notification.updated_at),
    }


def _authenticate_websocket_user(db: Session, token: str | None) -> User | None:
    if not token:
        return None

    try:
        user_id = int(get_subject_from_token(token, expected_type="access"))
    except (TypeError, ValueError):
        return None

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        return None
    return user


def build_notification_snapshot(db: Session, user_id: int) -> dict[str, Any]:
    notifications = list(
        db.scalars(
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc(), Notification.id.desc())
            .limit(50)
        ).all()
    )
    total_count = (
        db.scalar(
            select(func.count(Notification.id)).where(Notification.user_id == user_id)
        )
        or 0
    )
    unread_count = (
        db.scalar(
            select(func.count(Notification.id)).where(
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
            )
        )
        or 0
    )

    return {
        "total_count": total_count,
        "unread_count": unread_count,
        "latest_notification_id": notifications[0].id if notifications else None,
        "notifications": [
            _serialize_notification(notification) for notification in notifications
        ],
    }


def build_platform_snapshot(db: Session) -> dict[str, Any]:
    return {
        "users": db.scalar(select(func.count(User.id))) or 0,
        "teams": db.scalar(select(func.count(Team.id))) or 0,
        "tournaments": db.scalar(select(func.count(Tournament.id))) or 0,
        "tournament_matches": db.scalar(select(func.count(Match.id))) or 0,
        "ranked_matches": db.scalar(select(func.count(RankedMatch.id))) or 0,
        "open_disputes": db.scalar(
            select(func.count(MatchDispute.id)).where(
                MatchDispute.status == DisputeStatus.OPEN
            )
        )
        or 0,
        "completed_matches": db.scalar(
            select(func.count(Match.id)).where(Match.status == MatchStatus.COMPLETED)
        )
        or 0,
        "latest_match_id": db.scalar(select(func.max(Match.id))),
        "latest_tournament_id": db.scalar(select(func.max(Tournament.id))),
        "latest_ranked_match_id": db.scalar(select(func.max(RankedMatch.id))),
    }


def make_realtime_event(event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": event_type,
        "payload": payload,
        "created_at": datetime.now(UTC).isoformat(),
    }


def _snapshot_signature(snapshot: dict[str, Any]) -> tuple[int, int, int | None]:
    return (
        snapshot["total_count"],
        snapshot["unread_count"],
        snapshot["latest_notification_id"],
    )


def _platform_signature(snapshot: dict[str, Any]) -> tuple[Any, ...]:
    return tuple(snapshot.values())


async def stream_notifications(websocket: WebSocket, db: Session) -> None:
    user = _authenticate_websocket_user(db, websocket.query_params.get("token"))
    if user is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()
    last_signature: tuple[int, int, int | None] | None = None
    last_platform_signature: tuple[Any, ...] | None = None

    try:
        while True:
            db.expire_all()
            snapshot = build_notification_snapshot(db, user.id)
            signature = _snapshot_signature(snapshot)
            if signature != last_signature:
                await websocket.send_json(
                    make_realtime_event("notifications.snapshot", snapshot)
                )
                last_signature = signature

            platform_snapshot = build_platform_snapshot(db)
            platform_signature = _platform_signature(platform_snapshot)
            if platform_signature != last_platform_signature:
                await websocket.send_json(
                    make_realtime_event("platform.snapshot", platform_snapshot)
                )
                last_platform_signature = platform_signature

            try:
                message = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=NOTIFICATION_POLL_INTERVAL_SECONDS,
                )
            except TimeoutError:
                continue

            if message == "ping":
                await websocket.send_json(make_realtime_event("pong", {}))
    except WebSocketDisconnect:
        return
