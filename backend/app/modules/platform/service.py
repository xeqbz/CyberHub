from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.platform.model import (
    ActionLog,
    MatchmakingRequest,
    MatchmakingRequestStatus,
    Notification,
)


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
