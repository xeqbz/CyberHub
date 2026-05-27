import json
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session
from redis import Redis
from redis.exceptions import RedisError

from app.core.config import settings
from app.modules.platform.model import (
    ActionLog,
    MatchmakingRequest,
    MatchmakingRequestStatus,
    Notification,
)
from app.modules.users.model import User


DEFAULT_RANKINGS_CACHE_KEY = "cyberhub:rankings:default"
DEFAULT_RANKINGS_CACHE_TTL_SECONDS = 60


def record_action(
    db: Session,
    *,
    actor_id: int | None,
    action: str,
    entity_type: str,
    entity_id: int | None,
    details: dict | None = None,
) -> None:
    db.add(
        ActionLog(
            actor_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
        )
    )
    db.commit()


def create_notification(
    db: Session,
    *,
    user_id: int,
    title: str,
    message: str,
    related_entity_type: str | None = None,
    related_entity_id: int | None = None,
) -> Notification:
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        related_entity_type=related_entity_type,
        related_entity_id=related_entity_id,
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


def _get_redis_client() -> Redis:
    return Redis.from_url(
        settings.redis_dsn,
        decode_responses=True,
        socket_connect_timeout=0.1,
        socket_timeout=0.1,
    )


def build_default_ranking_rows(db: Session, *, limit: int = 100) -> list[dict]:
    users = list(
        db.scalars(
            select(User)
            .where(User.is_active.is_(True))
            .order_by(User.rating.desc(), User.wins.desc(), User.id)
            .limit(limit)
        ).all()
    )
    return [
        {
            "id": user.id,
            "username": user.username,
            "rating": user.rating,
            "wins": user.wins,
            "losses": user.losses,
            "draws": user.draws,
        }
        for user in users
    ]


def get_cached_default_rankings() -> list[dict] | None:
    try:
        payload = _get_redis_client().get(DEFAULT_RANKINGS_CACHE_KEY)
    except RedisError:
        return None

    if not payload:
        return None

    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        return None

    return data if isinstance(data, list) else None


def set_cached_default_rankings(
    rows: list[dict],
    *,
    ttl_seconds: int = DEFAULT_RANKINGS_CACHE_TTL_SECONDS,
) -> None:
    try:
        _get_redis_client().setex(
            DEFAULT_RANKINGS_CACHE_KEY,
            ttl_seconds,
            json.dumps(rows),
        )
    except RedisError:
        return


def invalidate_cached_default_rankings() -> None:
    try:
        _get_redis_client().delete(DEFAULT_RANKINGS_CACHE_KEY)
    except RedisError:
        return


def expire_stale_matchmaking_requests(
    db: Session,
    *,
    max_age_minutes: int = 30,
    now: datetime | None = None,
) -> int:
    cutoff = (now or datetime.now(UTC)) - timedelta(minutes=max_age_minutes)
    requests = list(
        db.scalars(
            select(MatchmakingRequest).where(
                MatchmakingRequest.status == MatchmakingRequestStatus.SEARCHING,
                MatchmakingRequest.created_at <= cutoff,
            )
        ).all()
    )

    for request in requests:
        request.status = MatchmakingRequestStatus.CANCELLED
        db.add(request)
        db.add(
            Notification(
                user_id=request.user_id,
                title="Matchmaking expired",
                message="Opponent search was cancelled because it took too long.",
                related_entity_type="matchmaking_request",
                related_entity_id=request.id,
            )
        )
        db.add(
            ActionLog(
                actor_id=None,
                action="ranked_matchmaking_expired",
                entity_type="matchmaking_request",
                entity_id=request.id,
                details={"max_age_minutes": max_age_minutes},
            )
        )

    if requests:
        db.commit()

    return len(requests)
