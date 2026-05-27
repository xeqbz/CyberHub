from app.celery_app import celery_app
from app.db.session import SessionLocal
from app.modules.platform.service import expire_stale_matchmaking_requests


@celery_app.task(name="platform.expire_stale_matchmaking_requests")
def expire_stale_matchmaking_requests_task(max_age_minutes: int = 30) -> int:
    # Diploma demo: Celery keeps the ranked matchmaking queue tidy via Redis.
    with SessionLocal() as db:
        return expire_stale_matchmaking_requests(
            db,
            max_age_minutes=max_age_minutes,
        )
