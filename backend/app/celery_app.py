from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "cyberhub",
    broker=settings.celery_broker_dsn,
    backend=settings.celery_result_backend_dsn,
    include=["app.modules.platform.tasks"],
)

celery_app.conf.update(
    accept_content=["json"],
    beat_schedule={
        "expire-stale-matchmaking-requests": {
            "task": "platform.expire_stale_matchmaking_requests",
            "schedule": 60.0,
            "args": (30,),
        },
        "auto-confirm-stale-match-results": {
            "task": "platform.auto_confirm_stale_match_results",
            "schedule": 300.0,
            "args": (24,),
        },
        "refresh-rankings-cache": {
            "task": "platform.refresh_rankings_cache",
            "schedule": 60.0,
        }
    },
    result_serializer="json",
    task_serializer="json",
    timezone="UTC",
)
