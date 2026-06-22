from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.celery_app import celery_app
from app.db.session import SessionLocal
from app.modules.matches.model import Match, MatchStatus
from app.modules.matches.repository import MatchRepository
from app.modules.matches.service import MatchResultNotPendingError, MatchService
from app.modules.platform.service import (
    build_default_ranking_rows,
    create_notification,
    expire_stale_matchmaking_requests,
    record_action,
    set_cached_default_rankings,
)
from app.modules.teams.repository import TeamRepository
from app.modules.tournaments.repository import TournamentRepository


@celery_app.task(name="platform.expire_stale_matchmaking_requests")
def expire_stale_matchmaking_requests_task(max_age_minutes: int = 30) -> int:
    # Diploma demo: Celery keeps the ranked matchmaking queue tidy via Redis.
    with SessionLocal() as db:
        return expire_stale_matchmaking_requests(
            db,
            max_age_minutes=max_age_minutes,
        )


@celery_app.task(name="platform.refresh_rankings_cache")
def refresh_rankings_cache_task() -> int:
    # Diploma demo: Redis keeps the default leaderboard warm for the frontend.
    with SessionLocal() as db:
        rows = build_default_ranking_rows(db)
        set_cached_default_rankings(rows)
        return len(rows)


@celery_app.task(name="platform.auto_confirm_stale_match_results")
def auto_confirm_stale_match_results_task(max_age_hours: int = 24) -> int:
    # Diploma demo: stale submitted results are auto-confirmed if nobody disputes.
    cutoff = datetime.now(UTC) - timedelta(hours=max_age_hours)
    confirmed = 0

    with SessionLocal() as db:
        service = MatchService(
            repository=MatchRepository(db),
            tournament_repository=TournamentRepository(db),
            team_repository=TeamRepository(db),
        )
        matches = list(
            db.scalars(
                select(Match).where(
                    Match.status == MatchStatus.PENDING_CONFIRMATION,
                    Match.result_submitted_at <= cutoff,
                )
            ).all()
        )

        for match in matches:
            try:
                confirmed_match = service.confirm_match_result(
                    match.id,
                    acting_user_id=match.tournament.owner_id,
                )
            except MatchResultNotPendingError:
                continue

            for team in (confirmed_match.home_team, confirmed_match.away_team):
                create_notification(
                    db,
                    user_id=team.owner_id,
                    title="Match result auto-confirmed",
                    message=(
                        f"Result for match #{confirmed_match.id} was "
                        "auto-confirmed after the review window expired."
                    ),
                    related_entity_type="match",
                    related_entity_id=confirmed_match.id,
                )
            record_action(
                db,
                actor_id=None,
                action="match_result_auto_confirmed",
                entity_type="match",
                entity_id=confirmed_match.id,
                details={"max_age_hours": max_age_hours},
            )
            confirmed += 1

    return confirmed
