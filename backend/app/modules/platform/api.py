import csv
from datetime import UTC, datetime
from io import StringIO

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_active_user, require_roles
from app.modules.matches.model import Match, MatchStatus
from app.modules.platform.model import (
    ActionLog,
    DisputeStatus,
    MatchDispute,
    MatchmakingRequest,
    MatchmakingRequestStatus,
    Notification,
    RankedMatch,
    RankedMatchStatus,
)
from app.modules.platform.schemas import (
    ActionLogRead,
    MatchDisputeCreate,
    MatchDisputeRead,
    MatchDisputeResolve,
    MatchmakingResponse,
    NotificationRead,
    OverviewStats,
    RankedMatchRead,
    RankedMatchScoreUpdate,
    RankingUser,
    TeamStats,
    TournamentStats,
)
from app.modules.platform.service import create_notification, record_action
from app.modules.teams.model import Team
from app.modules.tournaments.model import (
    Tournament,
    TournamentParticipant,
    TournamentParticipantStatus,
)
from app.modules.users.model import User, UserRole
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import UserRead, UserUpdate
from app.modules.users.service import (
    EmailAlreadyExistsError,
    UsernameAlreadyExistsError,
    UserNotFoundError,
    UserService,
)

router = APIRouter(tags=["platform"])
admin_router = APIRouter(prefix="/admin", tags=["admin"])


def _get_ranked_match(db: Session, match_id: int) -> RankedMatch | None:
    stmt = (
        select(RankedMatch)
        .where(RankedMatch.id == match_id)
        .options(
            joinedload(RankedMatch.player_one),
            joinedload(RankedMatch.player_two),
            joinedload(RankedMatch.winner),
        )
    )
    return db.scalar(stmt)


def _apply_elo(match: RankedMatch) -> None:
    player_one = match.player_one
    player_two = match.player_two
    rating_one = player_one.rating
    rating_two = player_two.rating

    expected_one = 1 / (1 + 10 ** ((rating_two - rating_one) / 400))
    expected_two = 1 / (1 + 10 ** ((rating_one - rating_two) / 400))

    if match.winner_id == player_one.id:
        score_one = 1.0
        score_two = 0.0
        player_one.wins += 1
        player_two.losses += 1
    elif match.winner_id == player_two.id:
        score_one = 0.0
        score_two = 1.0
        player_one.losses += 1
        player_two.wins += 1
    else:
        score_one = 0.5
        score_two = 0.5
        player_one.draws += 1
        player_two.draws += 1

    k_factor = 32
    player_one.rating = round(rating_one + k_factor * (score_one - expected_one))
    player_two.rating = round(rating_two + k_factor * (score_two - expected_two))


@router.get(
    "/rankings",
    response_model=list[RankingUser],
    status_code=status.HTTP_200_OK,
)
def list_rankings(
    search: str | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[User]:
    stmt = select(User).where(User.is_active.is_(True))

    if search:
        pattern = f"%{search.strip()}%"
        stmt = stmt.where(User.username.ilike(pattern))

    stmt = stmt.order_by(User.rating.desc(), User.wins.desc(), User.id).offset(offset)
    stmt = stmt.limit(limit)
    return list(db.scalars(stmt).all())


@router.get(
    "/statistics/overview",
    response_model=OverviewStats,
    status_code=status.HTTP_200_OK,
)
def get_statistics_overview(db: Session = Depends(get_db)) -> OverviewStats:
    users = db.scalar(select(func.count(User.id))) or 0
    teams = db.scalar(select(func.count(Team.id))) or 0
    tournaments = db.scalar(select(func.count(Tournament.id))) or 0
    tournament_matches = db.scalar(select(func.count(Match.id))) or 0
    ranked_matches = db.scalar(select(func.count(RankedMatch.id))) or 0
    open_disputes = (
        db.scalar(
            select(func.count(MatchDispute.id)).where(
                MatchDispute.status == DisputeStatus.OPEN
            )
        )
        or 0
    )
    completed_matches = (
        db.scalar(
            select(func.count(Match.id)).where(Match.status == MatchStatus.COMPLETED)
        )
        or 0
    )

    return OverviewStats(
        users=users,
        teams=teams,
        tournaments=tournaments,
        tournament_matches=tournament_matches,
        ranked_matches=ranked_matches,
        open_disputes=open_disputes,
        completed_matches=completed_matches,
    )


@router.get(
    "/statistics/teams",
    response_model=list[TeamStats],
    status_code=status.HTTP_200_OK,
)
def list_team_statistics(db: Session = Depends(get_db)) -> list[TeamStats]:
    teams = list(db.scalars(select(Team).order_by(Team.name)).all())
    matches = list(
        db.scalars(select(Match).where(Match.status == MatchStatus.COMPLETED)).all()
    )

    result: list[TeamStats] = []
    for team in teams:
        wins = 0
        losses = 0
        draws = 0
        total = 0

        for match in matches:
            if team.id not in {match.home_team_id, match.away_team_id}:
                continue

            total += 1
            if match.winner_team_id == team.id:
                wins += 1
            elif match.winner_team_id is None:
                draws += 1
            else:
                losses += 1

        result.append(
            TeamStats(
                team_id=team.id,
                name=team.name,
                matches=total,
                wins=wins,
                losses=losses,
                draws=draws,
            )
        )

    return result


@router.get(
    "/statistics/tournaments",
    response_model=list[TournamentStats],
    status_code=status.HTTP_200_OK,
)
def list_tournament_statistics(db: Session = Depends(get_db)) -> list[TournamentStats]:
    tournaments = list(db.scalars(select(Tournament).order_by(Tournament.id)).all())
    result: list[TournamentStats] = []

    for tournament in tournaments:
        participants = (
            db.scalar(
                select(func.count(TournamentParticipant.id)).where(
                    TournamentParticipant.tournament_id == tournament.id,
                    TournamentParticipant.status
                    == TournamentParticipantStatus.APPROVED,
                )
            )
            or 0
        )
        matches = (
            db.scalar(
                select(func.count(Match.id)).where(Match.tournament_id == tournament.id)
            )
            or 0
        )
        completed_matches = (
            db.scalar(
                select(func.count(Match.id)).where(
                    Match.tournament_id == tournament.id,
                    Match.status == MatchStatus.COMPLETED,
                )
            )
            or 0
        )

        result.append(
            TournamentStats(
                tournament_id=tournament.id,
                name=tournament.name,
                discipline=tournament.discipline,
                format=tournament.format,
                participants=participants,
                matches=matches,
                completed_matches=completed_matches,
            )
        )

    return result


@router.get(
    "/notifications",
    response_model=list[NotificationRead],
    status_code=status.HTTP_200_OK,
)
def list_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[Notification]:
    stmt = (
        select(Notification)
        .where(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(100)
    )
    return list(db.scalars(stmt).all())


@router.patch(
    "/notifications/{notification_id}/read",
    response_model=NotificationRead,
    status_code=status.HTTP_200_OK,
)
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Notification:
    notification = db.get(Notification, notification_id)
    if notification is None or notification.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    notification.is_read = True
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


@router.post(
    "/ranked/matchmaking",
    response_model=MatchmakingResponse,
    status_code=status.HTTP_200_OK,
)
def find_ranked_opponent(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> MatchmakingResponse:
    active_match = db.scalar(
        select(RankedMatch)
        .where(
            RankedMatch.status == RankedMatchStatus.SCHEDULED,
            or_(
                RankedMatch.player_one_id == current_user.id,
                RankedMatch.player_two_id == current_user.id,
            ),
        )
        .options(
            joinedload(RankedMatch.player_one),
            joinedload(RankedMatch.player_two),
            joinedload(RankedMatch.winner),
        )
        .order_by(RankedMatch.id.desc())
    )
    if active_match is not None:
        return MatchmakingResponse(
            status=MatchmakingRequestStatus.MATCHED,
            message="You already have an active ranked match",
            match=active_match,
        )

    own_request = db.scalar(
        select(MatchmakingRequest)
        .where(
            MatchmakingRequest.user_id == current_user.id,
            MatchmakingRequest.status == MatchmakingRequestStatus.SEARCHING,
        )
        .order_by(MatchmakingRequest.id.desc())
    )
    if own_request is not None:
        return MatchmakingResponse(
            status=MatchmakingRequestStatus.SEARCHING,
            message="Opponent search is already active",
            request=own_request,
        )

    opponent_request = db.scalar(
        select(MatchmakingRequest)
        .join(User, MatchmakingRequest.user_id == User.id)
        .where(
            MatchmakingRequest.user_id != current_user.id,
            MatchmakingRequest.status == MatchmakingRequestStatus.SEARCHING,
            User.is_active.is_(True),
        )
        .order_by(
            func.abs(MatchmakingRequest.rating_snapshot - current_user.rating),
            MatchmakingRequest.created_at,
        )
    )

    if opponent_request is None:
        request = MatchmakingRequest(
            user_id=current_user.id,
            rating_snapshot=current_user.rating,
        )
        db.add(request)
        db.commit()
        db.refresh(request)
        record_action(
            db,
            actor_id=current_user.id,
            action="ranked_matchmaking_started",
            entity_type="matchmaking_request",
            entity_id=request.id,
            details={"rating": current_user.rating},
        )
        return MatchmakingResponse(
            status=MatchmakingRequestStatus.SEARCHING,
            message="Searching for an opponent",
            request=request,
        )

    ranked_match = RankedMatch(
        player_one_id=opponent_request.user_id,
        player_two_id=current_user.id,
    )
    db.add(ranked_match)
    db.flush()

    opponent_request.status = MatchmakingRequestStatus.MATCHED
    opponent_request.matched_ranked_match_id = ranked_match.id
    current_request = MatchmakingRequest(
        user_id=current_user.id,
        status=MatchmakingRequestStatus.MATCHED,
        rating_snapshot=current_user.rating,
        matched_ranked_match_id=ranked_match.id,
    )
    db.add(current_request)
    db.commit()

    match = _get_ranked_match(db, ranked_match.id)
    if match is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create ranked match",
        )

    for user_id in {match.player_one_id, match.player_two_id}:
        create_notification(
            db,
            user_id=user_id,
            title="Ranked match found",
            message=f"Ranked match #{match.id} is ready.",
            related_entity_type="ranked_match",
            related_entity_id=match.id,
        )

    record_action(
        db,
        actor_id=current_user.id,
        action="ranked_match_created",
        entity_type="ranked_match",
        entity_id=match.id,
        details={
            "player_one_id": match.player_one_id,
            "player_two_id": match.player_two_id,
        },
    )

    return MatchmakingResponse(
        status=MatchmakingRequestStatus.MATCHED,
        message="Opponent found",
        match=match,
    )


@router.delete(
    "/ranked/matchmaking",
    status_code=status.HTTP_204_NO_CONTENT,
)
def cancel_ranked_matchmaking(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Response:
    request = db.scalar(
        select(MatchmakingRequest)
        .where(
            MatchmakingRequest.user_id == current_user.id,
            MatchmakingRequest.status == MatchmakingRequestStatus.SEARCHING,
        )
        .order_by(MatchmakingRequest.id.desc())
    )
    if request is not None:
        request.status = MatchmakingRequestStatus.CANCELLED
        db.add(request)
        db.commit()
        record_action(
            db,
            actor_id=current_user.id,
            action="ranked_matchmaking_cancelled",
            entity_type="matchmaking_request",
            entity_id=request.id,
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/ranked/matches",
    response_model=list[RankedMatchRead],
    status_code=status.HTTP_200_OK,
)
def list_my_ranked_matches(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[RankedMatch]:
    stmt = (
        select(RankedMatch)
        .where(
            or_(
                RankedMatch.player_one_id == current_user.id,
                RankedMatch.player_two_id == current_user.id,
            )
        )
        .options(
            joinedload(RankedMatch.player_one),
            joinedload(RankedMatch.player_two),
            joinedload(RankedMatch.winner),
        )
        .order_by(RankedMatch.created_at.desc())
    )
    return list(db.scalars(stmt).unique().all())


@router.patch(
    "/ranked/matches/{match_id}/result",
    response_model=RankedMatchRead,
    status_code=status.HTTP_200_OK,
)
def submit_ranked_match_result(
    match_id: int,
    payload: RankedMatchScoreUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> RankedMatch:
    match = _get_ranked_match(db, match_id)
    if match is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ranked match not found",
        )
    if current_user.id not in {match.player_one_id, match.player_two_id}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only match participants can submit the result",
        )
    if match.status == RankedMatchStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ranked match is already completed",
        )

    match.player_one_score = payload.player_one_score
    match.player_two_score = payload.player_two_score
    if payload.player_one_score > payload.player_two_score:
        match.winner_id = match.player_one_id
    elif payload.player_two_score > payload.player_one_score:
        match.winner_id = match.player_two_id
    else:
        match.winner_id = None

    match.status = RankedMatchStatus.COMPLETED
    match.completed_at = datetime.now(UTC)
    _apply_elo(match)

    db.add(match)
    db.add(match.player_one)
    db.add(match.player_two)
    db.commit()

    for user_id in {match.player_one_id, match.player_two_id}:
        create_notification(
            db,
            user_id=user_id,
            title="Ranked result confirmed",
            message=f"Ranked match #{match.id} has been completed.",
            related_entity_type="ranked_match",
            related_entity_id=match.id,
        )

    record_action(
        db,
        actor_id=current_user.id,
        action="ranked_match_completed",
        entity_type="ranked_match",
        entity_id=match.id,
        details={
            "player_one_score": payload.player_one_score,
            "player_two_score": payload.player_two_score,
            "winner_id": match.winner_id,
        },
    )

    refreshed = _get_ranked_match(db, match.id)
    if refreshed is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh ranked match",
        )
    return refreshed


@router.post(
    "/disputes",
    response_model=MatchDisputeRead,
    status_code=status.HTTP_201_CREATED,
)
def create_match_dispute(
    payload: MatchDisputeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> MatchDispute:
    match = db.get(Match, payload.match_id)
    if match is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found",
        )

    existing = db.scalar(
        select(MatchDispute).where(
            MatchDispute.match_id == payload.match_id,
            MatchDispute.opened_by_id == current_user.id,
        )
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already created a dispute for this match",
        )

    dispute = MatchDispute(
        match_id=payload.match_id,
        opened_by_id=current_user.id,
        reason=payload.reason.strip(),
    )
    db.add(dispute)
    db.commit()
    db.refresh(dispute)

    record_action(
        db,
        actor_id=current_user.id,
        action="match_dispute_opened",
        entity_type="match_dispute",
        entity_id=dispute.id,
        details={"match_id": payload.match_id},
    )

    stmt = (
        select(MatchDispute)
        .where(MatchDispute.id == dispute.id)
        .options(
            joinedload(MatchDispute.opened_by),
            joinedload(MatchDispute.resolved_by),
            joinedload(MatchDispute.match).joinedload(Match.tournament),
            joinedload(MatchDispute.match).joinedload(Match.home_team),
            joinedload(MatchDispute.match).joinedload(Match.away_team),
            joinedload(MatchDispute.match).joinedload(Match.winner_team),
        )
    )
    return db.scalar(stmt)


@router.get(
    "/disputes",
    response_model=list[MatchDisputeRead],
    status_code=status.HTTP_200_OK,
)
def list_my_disputes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[MatchDispute]:
    stmt = (
        select(MatchDispute)
        .where(MatchDispute.opened_by_id == current_user.id)
        .options(
            joinedload(MatchDispute.opened_by),
            joinedload(MatchDispute.resolved_by),
            joinedload(MatchDispute.match).joinedload(Match.tournament),
            joinedload(MatchDispute.match).joinedload(Match.home_team),
            joinedload(MatchDispute.match).joinedload(Match.away_team),
            joinedload(MatchDispute.match).joinedload(Match.winner_team),
        )
        .order_by(MatchDispute.created_at.desc())
    )
    return list(db.scalars(stmt).unique().all())


@admin_router.get(
    "/users",
    response_model=list[UserRead],
    status_code=status.HTTP_200_OK,
)
def admin_list_users(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
) -> list[User]:
    service = UserService(UserRepository(db))
    record_action(
        db,
        actor_id=current_user.id,
        action="admin_users_viewed",
        entity_type="user",
        entity_id=None,
    )
    return service.list_users(offset=offset, limit=limit)


@admin_router.post(
    "/bootstrap",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
)
def bootstrap_first_admin(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> User:
    admin_count = (
        db.scalar(select(func.count(User.id)).where(User.role == UserRole.ADMIN)) or 0
    )
    if admin_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An administrator already exists",
        )

    current_user.role = UserRole.ADMIN
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    record_action(
        db,
        actor_id=current_user.id,
        action="admin_bootstrapped",
        entity_type="user",
        entity_id=current_user.id,
    )
    return current_user


@admin_router.patch(
    "/users/{user_id}",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
)
def admin_update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
) -> User:
    service = UserService(UserRepository(db))
    try:
        user = service.update_user(user_id, payload)
    except UserNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        ) from exc
    except UsernameAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username is already in use",
        ) from exc
    except EmailAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already in use",
        ) from exc

    record_action(
        db,
        actor_id=current_user.id,
        action="admin_user_updated",
        entity_type="user",
        entity_id=user.id,
        details={
            "is_active": payload.is_active,
            "role": payload.role,
        },
    )
    return user


@admin_router.get(
    "/disputes",
    response_model=list[MatchDisputeRead],
    status_code=status.HTTP_200_OK,
)
def admin_list_disputes(
    status_filter: DisputeStatus | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
) -> list[MatchDispute]:
    stmt = select(MatchDispute).options(
        joinedload(MatchDispute.opened_by),
        joinedload(MatchDispute.resolved_by),
        joinedload(MatchDispute.match).joinedload(Match.tournament),
        joinedload(MatchDispute.match).joinedload(Match.home_team),
        joinedload(MatchDispute.match).joinedload(Match.away_team),
        joinedload(MatchDispute.match).joinedload(Match.winner_team),
    )
    if status_filter is not None:
        stmt = stmt.where(MatchDispute.status == status_filter)
    stmt = stmt.order_by(MatchDispute.created_at.desc())

    record_action(
        db,
        actor_id=current_user.id,
        action="admin_disputes_viewed",
        entity_type="match_dispute",
        entity_id=None,
    )
    return list(db.scalars(stmt).unique().all())


@admin_router.patch(
    "/disputes/{dispute_id}/resolve",
    response_model=MatchDisputeRead,
    status_code=status.HTTP_200_OK,
)
def admin_resolve_dispute(
    dispute_id: int,
    payload: MatchDisputeResolve,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
) -> MatchDispute:
    dispute = db.get(MatchDispute, dispute_id)
    if dispute is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dispute not found",
        )

    dispute.status = payload.status
    dispute.resolution = payload.resolution.strip()
    dispute.resolved_by_id = current_user.id
    dispute.resolved_at = datetime.now(UTC)
    db.add(dispute)
    db.commit()

    create_notification(
        db,
        user_id=dispute.opened_by_id,
        title="Dispute reviewed",
        message=f"Your dispute #{dispute.id} was marked as {dispute.status}.",
        related_entity_type="match_dispute",
        related_entity_id=dispute.id,
    )
    record_action(
        db,
        actor_id=current_user.id,
        action="admin_dispute_resolved",
        entity_type="match_dispute",
        entity_id=dispute.id,
        details={"status": dispute.status, "resolution": dispute.resolution},
    )

    stmt = (
        select(MatchDispute)
        .where(MatchDispute.id == dispute.id)
        .options(
            joinedload(MatchDispute.opened_by),
            joinedload(MatchDispute.resolved_by),
            joinedload(MatchDispute.match).joinedload(Match.tournament),
            joinedload(MatchDispute.match).joinedload(Match.home_team),
            joinedload(MatchDispute.match).joinedload(Match.away_team),
            joinedload(MatchDispute.match).joinedload(Match.winner_team),
        )
    )
    return db.scalar(stmt)


@admin_router.get(
    "/action-logs",
    response_model=list[ActionLogRead],
    status_code=status.HTTP_200_OK,
)
def admin_list_action_logs(
    action: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
) -> list[ActionLog]:
    stmt = select(ActionLog).options(joinedload(ActionLog.actor))
    if action:
        stmt = stmt.where(ActionLog.action == action.strip())
    stmt = stmt.order_by(ActionLog.created_at.desc()).limit(200)

    record_action(
        db,
        actor_id=current_user.id,
        action="admin_action_logs_viewed",
        entity_type="action_log",
        entity_id=None,
    )
    return list(db.scalars(stmt).unique().all())


def _build_report_rows(db: Session, report_type: str) -> list[dict[str, object]]:
    if report_type == "users":
        users = db.scalars(select(User).order_by(User.id)).all()
        return [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "is_active": user.is_active,
                "rating": user.rating,
                "wins": user.wins,
                "losses": user.losses,
                "draws": user.draws,
            }
            for user in users
        ]

    if report_type == "tournaments":
        tournaments = db.scalars(select(Tournament).order_by(Tournament.id)).all()
        return [
            {
                "id": tournament.id,
                "name": tournament.name,
                "discipline": tournament.discipline,
                "format": tournament.format,
                "status": tournament.status,
                "max_teams": tournament.max_teams,
                "starts_at": tournament.starts_at,
            }
            for tournament in tournaments
        ]

    if report_type == "matches":
        matches = db.scalars(select(Match).order_by(Match.id)).all()
        return [
            {
                "id": match.id,
                "tournament_id": match.tournament_id,
                "home_team_id": match.home_team_id,
                "away_team_id": match.away_team_id,
                "status": match.status,
                "home_score": match.home_score,
                "away_score": match.away_score,
                "winner_team_id": match.winner_team_id,
            }
            for match in matches
        ]

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Unsupported report type",
    )


@admin_router.get(
    "/reports/export",
    status_code=status.HTTP_200_OK,
)
def admin_export_report(
    report_type: str = Query(
        default="tournaments",
        pattern="^(users|tournaments|matches)$",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.ORGANIZER)),
) -> StreamingResponse:
    rows = _build_report_rows(db, report_type)
    output = StringIO()

    fieldnames = list(rows[0].keys()) if rows else ["empty"]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    output.seek(0)

    record_action(
        db,
        actor_id=current_user.id,
        action="report_exported",
        entity_type="report",
        entity_id=None,
        details={"report_type": report_type},
    )

    filename = f"cyberhub-{report_type}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


router.include_router(admin_router)
