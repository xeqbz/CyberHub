from __future__ import annotations

import argparse
from datetime import UTC, datetime, timedelta
from functools import lru_cache

from sqlalchemy import delete, or_, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.modules.auth.security import hash_password
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
from app.modules.teams.model import Team, TeamMember, TeamMemberRole
from app.modules.tournaments.model import (
    Tournament,
    TournamentParticipant,
    TournamentParticipantStatus,
    TournamentStatus,
)
from app.modules.users.model import User, UserRole

DEMO_DOMAIN = "cyberhub-demo.com"
DEMO_EMAIL_SUFFIX = f"@{DEMO_DOMAIN}"
DEMO_NAME_PREFIX = "Demo "
DEMO_PASSWORD = "demo12345"
DEMO_PLAYER_COUNT = 60
DEMO_TEAM_SIZE = 5

DEMO_ACTIONS = {
    "demo_admin_bootstrap",
    "demo_dispute_opened",
    "demo_dispute_resolved",
    "demo_match_result_confirmed",
    "demo_ranked_match_completed",
    "demo_tournament_created",
    "demo_tournament_registration_reviewed",
}


@lru_cache(maxsize=1)
def demo_password_hash() -> str:
    return hash_password(DEMO_PASSWORD)


def now_utc() -> datetime:
    return datetime.now(UTC)


def get_or_create_user(
    db: Session,
    *,
    username: str,
    email: str,
    role: UserRole = UserRole.USER,
    rating: int = 1000,
    wins: int = 0,
    losses: int = 0,
    draws: int = 0,
) -> User:
    user = db.scalar(
        select(User).where(or_(User.email == email, User.username == username))
    )
    if user is None:
        user = User(
            username=username,
            email=email,
            hashed_password=demo_password_hash(),
        )
        db.add(user)

    user.username = username
    user.email = email
    user.hashed_password = demo_password_hash()
    user.role = role
    user.is_active = True
    user.rating = rating
    user.wins = wins
    user.losses = losses
    user.draws = draws
    db.flush()
    return user


def ensure_team_member(
    db: Session,
    *,
    team: Team,
    user: User,
    role: TeamMemberRole,
) -> TeamMember:
    member = db.scalar(
        select(TeamMember).where(
            TeamMember.team_id == team.id,
            TeamMember.user_id == user.id,
        )
    )
    if member is None:
        member = TeamMember(team_id=team.id, user_id=user.id)
        db.add(member)

    member.role = role
    db.flush()
    return member


def get_or_create_team(
    db: Session,
    *,
    name: str,
    description: str,
    owner: User,
    members: list[User],
) -> Team:
    team = db.scalar(select(Team).where(Team.name == name))
    if team is None:
        team = Team(name=name, description=description, owner_id=owner.id)
        db.add(team)

    team.description = description
    team.owner_id = owner.id
    db.flush()

    ensure_team_member(db, team=team, user=owner, role=TeamMemberRole.OWNER)
    for member in members:
        ensure_team_member(db, team=team, user=member, role=TeamMemberRole.MEMBER)

    desired_member_ids = {owner.id, *(member.id for member in members)}
    db.execute(
        delete(TeamMember).where(
            TeamMember.team_id == team.id,
            ~TeamMember.user_id.in_(desired_member_ids),
        )
    )
    db.flush()
    return team


def get_or_create_tournament(
    db: Session,
    *,
    name: str,
    owner: User,
    status: TournamentStatus,
    description: str,
    max_teams: int,
    starts_at: datetime | None,
    discipline: str = "CS2",
    format_: str = "single_elimination",
    rules: str | None = None,
    bracket_settings: dict | None = None,
) -> Tournament:
    tournament = db.scalar(select(Tournament).where(Tournament.name == name))
    if tournament is None:
        tournament = Tournament(name=name, owner_id=owner.id)
        db.add(tournament)

    tournament.description = description
    tournament.owner_id = owner.id
    tournament.status = status
    tournament.format = format_
    tournament.discipline = discipline
    tournament.rules = rules or "Best of 3. Map veto before each match."
    tournament.bracket_settings = bracket_settings or {
        "seeded": True,
        "third_place_match": False,
        "demo": True,
    }
    tournament.max_teams = max_teams
    tournament.starts_at = starts_at
    db.flush()
    return tournament


def ensure_participant(
    db: Session,
    *,
    tournament: Tournament,
    team: Team,
    status: TournamentParticipantStatus,
    decided_by: User | None = None,
) -> TournamentParticipant:
    participant = db.scalar(
        select(TournamentParticipant).where(
            TournamentParticipant.tournament_id == tournament.id,
            TournamentParticipant.team_id == team.id,
        )
    )
    if participant is None:
        participant = TournamentParticipant(
            tournament_id=tournament.id,
            team_id=team.id,
        )
        db.add(participant)

    participant.status = status
    if status == TournamentParticipantStatus.PENDING:
        participant.decided_by_id = None
        participant.decided_at = None
    else:
        participant.decided_by_id = decided_by.id if decided_by else tournament.owner_id
        participant.decided_at = now_utc()
    db.flush()
    return participant


def get_or_create_match(
    db: Session,
    *,
    tournament: Tournament,
    home_team: Team,
    away_team: Team,
    bracket_position: int,
    status: MatchStatus,
    stage: str = "Main bracket",
    round_number: int = 1,
    scheduled_at: datetime | None = None,
    completed_at: datetime | None = None,
    home_score: int | None = None,
    away_score: int | None = None,
    winner_team: Team | None = None,
    confirmed_by: User | None = None,
) -> Match:
    match = db.scalar(
        select(Match).where(
            Match.tournament_id == tournament.id,
            Match.round_number == round_number,
            Match.bracket_position == bracket_position,
        )
    )
    if match is None:
        match = Match(
            tournament_id=tournament.id,
            home_team_id=home_team.id,
            away_team_id=away_team.id,
            bracket_position=bracket_position,
            round_number=round_number,
        )
        db.add(match)

    match.home_team_id = home_team.id
    match.away_team_id = away_team.id
    match.status = status
    match.stage = stage
    match.round_number = round_number
    match.bracket_position = bracket_position
    match.scheduled_at = scheduled_at
    match.home_score = home_score
    match.away_score = away_score
    match.winner_team_id = winner_team.id if winner_team else None
    match.result_confirmed_by_id = confirmed_by.id if confirmed_by else None
    match.completed_at = (
        completed_at
        if completed_at is not None
        else now_utc()
        if status == MatchStatus.COMPLETED
        else None
    )
    db.flush()
    return match


def get_or_create_ranked_match(
    db: Session,
    *,
    player_one: User,
    player_two: User,
    status: RankedMatchStatus,
    player_one_score: int | None = None,
    player_two_score: int | None = None,
    player_one_kills: int = 0,
    player_one_deaths: int = 0,
    player_one_assists: int = 0,
    player_two_kills: int = 0,
    player_two_deaths: int = 0,
    player_two_assists: int = 0,
    winner: User | None = None,
    completed_at: datetime | None = None,
) -> RankedMatch:
    match = db.scalar(
        select(RankedMatch).where(
            RankedMatch.player_one_id == player_one.id,
            RankedMatch.player_two_id == player_two.id,
        )
    )
    if match is None:
        match = RankedMatch(player_one_id=player_one.id, player_two_id=player_two.id)
        db.add(match)

    match.status = status
    match.player_one_score = player_one_score
    match.player_two_score = player_two_score
    match.player_one_kills = player_one_kills
    match.player_one_deaths = player_one_deaths
    match.player_one_assists = player_one_assists
    match.player_two_kills = player_two_kills
    match.player_two_deaths = player_two_deaths
    match.player_two_assists = player_two_assists
    match.winner_id = winner.id if winner else None
    match.completed_at = (
        completed_at
        if completed_at is not None
        else now_utc()
        if status == RankedMatchStatus.COMPLETED
        else None
    )
    db.flush()
    return match


def ensure_matchmaking_request(
    db: Session,
    *,
    user: User,
    status: MatchmakingRequestStatus,
    ranked_match: RankedMatch | None = None,
) -> MatchmakingRequest:
    request = db.scalar(
        select(MatchmakingRequest).where(
            MatchmakingRequest.user_id == user.id,
            MatchmakingRequest.status == status,
        )
    )
    if request is None:
        request = MatchmakingRequest(user_id=user.id, status=status)
        db.add(request)

    request.rating_snapshot = user.rating
    request.matched_ranked_match_id = ranked_match.id if ranked_match else None
    db.flush()
    return request


def ensure_notification(
    db: Session,
    *,
    user: User,
    title: str,
    message: str,
    related_entity_type: str | None = None,
    related_entity_id: int | None = None,
    is_read: bool = False,
) -> Notification:
    notification = db.scalar(
        select(Notification).where(
            Notification.user_id == user.id,
            Notification.title == title,
            Notification.related_entity_type == related_entity_type,
            Notification.related_entity_id == related_entity_id,
        )
    )
    if notification is None:
        notification = Notification(user_id=user.id, title=title)
        db.add(notification)

    notification.message = message
    notification.related_entity_type = related_entity_type
    notification.related_entity_id = related_entity_id
    notification.is_read = is_read
    db.flush()
    return notification


def ensure_dispute(
    db: Session,
    *,
    match: Match,
    opened_by: User,
    status: DisputeStatus,
    reason: str,
    resolved_by: User | None = None,
    resolution: str | None = None,
) -> MatchDispute:
    dispute = db.scalar(
        select(MatchDispute).where(
            MatchDispute.match_id == match.id,
            MatchDispute.opened_by_id == opened_by.id,
        )
    )
    if dispute is None:
        dispute = MatchDispute(match_id=match.id, opened_by_id=opened_by.id)
        db.add(dispute)

    dispute.reason = reason
    dispute.status = status
    dispute.resolution = resolution
    dispute.resolved_by_id = resolved_by.id if resolved_by else None
    dispute.resolved_at = now_utc() if resolved_by else None
    db.flush()
    return dispute


def ensure_action_log(
    db: Session,
    *,
    actor: User | None,
    action: str,
    entity_type: str,
    entity_id: int | None,
    details: dict | None = None,
) -> ActionLog:
    log = db.scalar(
        select(ActionLog).where(
            ActionLog.action == action,
            ActionLog.entity_type == entity_type,
            ActionLog.entity_id == entity_id,
        )
    )
    if log is None:
        log = ActionLog(action=action, entity_type=entity_type, entity_id=entity_id)
        db.add(log)

    log.actor_id = actor.id if actor else None
    log.details = details
    db.flush()
    return log


def list_ids(db: Session, stmt) -> list[int]:
    return list(db.scalars(stmt).all())


def delete_matching(db: Session, model, conditions: list) -> None:
    filtered_conditions = [
        condition for condition in conditions if condition is not None
    ]
    if filtered_conditions:
        db.execute(delete(model).where(or_(*filtered_conditions)))


def purge_demo_data(db: Session) -> dict[str, int]:
    demo_user_ids = list_ids(
        db,
        select(User.id).where(
            or_(
                User.email.like(f"%{DEMO_EMAIL_SUFFIX}"),
                User.username.like("demo_%"),
            )
        ),
    )

    team_conditions = [Team.name.like(f"{DEMO_NAME_PREFIX}%")]
    if demo_user_ids:
        team_conditions.append(Team.owner_id.in_(demo_user_ids))
    demo_team_ids = list_ids(db, select(Team.id).where(or_(*team_conditions)))

    tournament_conditions = [Tournament.name.like(f"{DEMO_NAME_PREFIX}%")]
    if demo_user_ids:
        tournament_conditions.append(Tournament.owner_id.in_(demo_user_ids))
    demo_tournament_ids = list_ids(
        db,
        select(Tournament.id).where(or_(*tournament_conditions)),
    )

    match_conditions = []
    if demo_tournament_ids:
        match_conditions.append(Match.tournament_id.in_(demo_tournament_ids))
    if demo_team_ids:
        match_conditions.extend(
            [
                Match.home_team_id.in_(demo_team_ids),
                Match.away_team_id.in_(demo_team_ids),
            ]
        )
    demo_match_ids = (
        list_ids(db, select(Match.id).where(or_(*match_conditions)))
        if match_conditions
        else []
    )

    ranked_match_conditions = []
    if demo_user_ids:
        ranked_match_conditions.extend(
            [
                RankedMatch.player_one_id.in_(demo_user_ids),
                RankedMatch.player_two_id.in_(demo_user_ids),
                RankedMatch.winner_id.in_(demo_user_ids),
            ]
        )
    demo_ranked_match_ids = (
        list_ids(db, select(RankedMatch.id).where(or_(*ranked_match_conditions)))
        if ranked_match_conditions
        else []
    )

    dispute_conditions = []
    if demo_match_ids:
        dispute_conditions.append(MatchDispute.match_id.in_(demo_match_ids))
    if demo_user_ids:
        dispute_conditions.extend(
            [
                MatchDispute.opened_by_id.in_(demo_user_ids),
                MatchDispute.resolved_by_id.in_(demo_user_ids),
            ]
        )
    demo_dispute_ids = (
        list_ids(db, select(MatchDispute.id).where(or_(*dispute_conditions)))
        if dispute_conditions
        else []
    )

    notification_conditions = []
    if demo_user_ids:
        notification_conditions.append(Notification.user_id.in_(demo_user_ids))
    if demo_tournament_ids:
        notification_conditions.append(
            (Notification.related_entity_type == "tournament")
            & Notification.related_entity_id.in_(demo_tournament_ids)
        )
    if demo_match_ids:
        notification_conditions.append(
            (Notification.related_entity_type == "match")
            & Notification.related_entity_id.in_(demo_match_ids)
        )
    if demo_dispute_ids:
        notification_conditions.append(
            (Notification.related_entity_type == "match_dispute")
            & Notification.related_entity_id.in_(demo_dispute_ids)
        )
    if demo_ranked_match_ids:
        notification_conditions.append(
            (Notification.related_entity_type == "ranked_match")
            & Notification.related_entity_id.in_(demo_ranked_match_ids)
        )
    delete_matching(db, Notification, notification_conditions)

    action_log_conditions = [ActionLog.action.in_(DEMO_ACTIONS)]
    if demo_user_ids:
        action_log_conditions.append(ActionLog.actor_id.in_(demo_user_ids))
    if demo_tournament_ids:
        action_log_conditions.append(
            (ActionLog.entity_type == "tournament")
            & ActionLog.entity_id.in_(demo_tournament_ids)
        )
    if demo_match_ids:
        action_log_conditions.append(
            (ActionLog.entity_type == "match")
            & ActionLog.entity_id.in_(demo_match_ids)
        )
    if demo_dispute_ids:
        action_log_conditions.append(
            (ActionLog.entity_type == "match_dispute")
            & ActionLog.entity_id.in_(demo_dispute_ids)
        )
    if demo_ranked_match_ids:
        action_log_conditions.append(
            (ActionLog.entity_type == "ranked_match")
            & ActionLog.entity_id.in_(demo_ranked_match_ids)
        )
    delete_matching(db, ActionLog, action_log_conditions)

    delete_matching(db, MatchDispute, dispute_conditions)

    matchmaking_conditions = []
    if demo_user_ids:
        matchmaking_conditions.append(MatchmakingRequest.user_id.in_(demo_user_ids))
    if demo_ranked_match_ids:
        matchmaking_conditions.append(
            MatchmakingRequest.matched_ranked_match_id.in_(demo_ranked_match_ids)
        )
    delete_matching(db, MatchmakingRequest, matchmaking_conditions)

    delete_matching(db, RankedMatch, [RankedMatch.id.in_(demo_ranked_match_ids)])
    delete_matching(db, Match, [Match.id.in_(demo_match_ids)])
    delete_matching(
        db,
        TournamentParticipant,
        [
            TournamentParticipant.tournament_id.in_(demo_tournament_ids),
            TournamentParticipant.team_id.in_(demo_team_ids),
        ],
    )
    delete_matching(db, Tournament, [Tournament.id.in_(demo_tournament_ids)])
    delete_matching(
        db,
        TeamMember,
        [
            TeamMember.team_id.in_(demo_team_ids),
            TeamMember.user_id.in_(demo_user_ids),
        ],
    )
    delete_matching(db, Team, [Team.id.in_(demo_team_ids)])
    delete_matching(db, User, [User.id.in_(demo_user_ids)])

    db.flush()
    return {
        "purged_users": len(demo_user_ids),
        "purged_teams": len(demo_team_ids),
        "purged_tournaments": len(demo_tournament_ids),
        "purged_matches": len(demo_match_ids),
        "purged_ranked_matches": len(demo_ranked_match_ids),
        "purged_disputes": len(demo_dispute_ids),
    }


def create_demo_users(db: Session) -> tuple[dict[str, User], list[User]]:
    users: dict[str, User] = {}
    users["admin"] = get_or_create_user(
        db,
        username="demo_admin",
        email=f"admin{DEMO_EMAIL_SUFFIX}",
        role=UserRole.ADMIN,
        rating=1540,
        wins=24,
        losses=8,
        draws=2,
    )
    users["moderator"] = get_or_create_user(
        db,
        username="demo_moderator",
        email=f"moderator{DEMO_EMAIL_SUFFIX}",
        role=UserRole.ADMIN,
        rating=1325,
        wins=14,
        losses=10,
        draws=1,
    )
    users["organizer"] = get_or_create_user(
        db,
        username="demo_organizer",
        email=f"organizer{DEMO_EMAIL_SUFFIX}",
        role=UserRole.ORGANIZER,
        rating=1290,
        wins=15,
        losses=12,
        draws=1,
    )
    users["league_ops"] = get_or_create_user(
        db,
        username="demo_league_ops",
        email=f"league.ops{DEMO_EMAIL_SUFFIX}",
        role=UserRole.ORGANIZER,
        rating=1215,
        wins=11,
        losses=13,
        draws=3,
    )

    legacy_players = [
        ("demo_player", "player", 1495, 28, 12, 3),
        ("demo_rival", "rival", 1460, 25, 15, 1),
        ("demo_support", "support", 1175, 12, 20, 4),
        ("demo_captain", "captain", 1535, 31, 10, 2),
    ]

    players: list[User] = []
    for index, (username, email_name, rating, wins, losses, draws) in enumerate(
        legacy_players
    ):
        player = get_or_create_user(
            db,
            username=username,
            email=f"{email_name}{DEMO_EMAIL_SUFFIX}",
            rating=rating,
            wins=wins,
            losses=losses,
            draws=draws,
        )
        users[f"player_{index + 1}"] = player
        players.append(player)

    for index in range(1, DEMO_PLAYER_COUNT - len(legacy_players) + 1):
        rating = 940 + ((index * 43) % 720)
        wins = 5 + ((index * 7) % 34)
        losses = 3 + ((index * 5) % 24)
        draws = index % 4 if index % 6 == 0 else 0
        player = get_or_create_user(
            db,
            username=f"demo_player_{index:02d}",
            email=f"player{index:02d}{DEMO_EMAIL_SUFFIX}",
            rating=rating,
            wins=wins,
            losses=losses,
            draws=draws,
        )
        users[f"player_{len(players) + 1}"] = player
        players.append(player)

    return users, players


def create_demo_teams(db: Session, players: list[User]) -> list[Team]:
    team_names = [
        "Demo Neon Core",
        "Demo Byte Forge",
        "Demo Quantum Stack",
        "Demo Vector Pulse",
        "Demo Signal Prime",
        "Demo Cipher Unit",
        "Demo Radiant LAN",
        "Demo Metro Sync",
        "Demo Atlas Five",
        "Demo Flux Arena",
        "Demo Nova Circuit",
        "Demo Skyline Boost",
    ]

    teams: list[Team] = []
    for index, name in enumerate(team_names):
        roster = players[index * DEMO_TEAM_SIZE : (index + 1) * DEMO_TEAM_SIZE]
        owner = roster[0]
        members = roster[1:]
        team = get_or_create_team(
            db,
            name=name,
            description=(
                f"Full five-player demo roster #{index + 1} for screenshots, "
                "tournament entries and match history."
            ),
            owner=owner,
            members=members,
        )
        teams.append(team)

    return teams


def approve_teams(
    db: Session,
    *,
    tournament: Tournament,
    teams: list[Team],
    decided_by: User,
) -> None:
    for team in teams:
        ensure_participant(
            db,
            tournament=tournament,
            team=team,
            status=TournamentParticipantStatus.APPROVED,
            decided_by=decided_by,
        )


def create_bracket_settings(
    *,
    teams_count: int,
    seeded: bool = True,
    third_place_match: bool = False,
    bracket_type: str = "single_elimination",
) -> dict:
    return {
        "demo": True,
        "type": bracket_type,
        "teams_count": teams_count,
        "seeded": seeded,
        "third_place_match": third_place_match,
    }


def create_demo_tournaments(
    db: Session,
    *,
    organizer: User,
    league_ops: User,
    teams: list[Team],
) -> tuple[list[Tournament], list[Match]]:
    current_time = now_utc()
    tournaments: list[Tournament] = []
    matches: list[Match] = []

    masters = get_or_create_tournament(
        db,
        name="Demo CyberHub Masters",
        owner=organizer,
        status=TournamentStatus.IN_PROGRESS,
        description=(
            "Main showcase tournament with approved teams, completed semifinals "
            "and a scheduled final."
        ),
        max_teams=16,
        starts_at=current_time - timedelta(days=2),
        bracket_settings=create_bracket_settings(
            teams_count=8,
            third_place_match=True,
        ),
    )
    tournaments.append(masters)
    masters_teams = teams[:8]
    approve_teams(db, tournament=masters, teams=masters_teams, decided_by=organizer)
    matches.extend(
        [
            get_or_create_match(
                db,
                tournament=masters,
                home_team=masters_teams[0],
                away_team=masters_teams[7],
                bracket_position=1,
                round_number=1,
                stage="Quarterfinal",
                status=MatchStatus.COMPLETED,
                scheduled_at=current_time - timedelta(days=2, hours=6),
                completed_at=current_time - timedelta(days=2, hours=4),
                home_score=2,
                away_score=0,
                winner_team=masters_teams[0],
                confirmed_by=organizer,
            ),
            get_or_create_match(
                db,
                tournament=masters,
                home_team=masters_teams[1],
                away_team=masters_teams[6],
                bracket_position=2,
                round_number=1,
                stage="Quarterfinal",
                status=MatchStatus.COMPLETED,
                scheduled_at=current_time - timedelta(days=2, hours=4),
                completed_at=current_time - timedelta(days=2, hours=2),
                home_score=2,
                away_score=1,
                winner_team=masters_teams[1],
                confirmed_by=organizer,
            ),
            get_or_create_match(
                db,
                tournament=masters,
                home_team=masters_teams[2],
                away_team=masters_teams[5],
                bracket_position=3,
                round_number=1,
                stage="Quarterfinal",
                status=MatchStatus.COMPLETED,
                scheduled_at=current_time - timedelta(days=1, hours=8),
                completed_at=current_time - timedelta(days=1, hours=6),
                home_score=1,
                away_score=2,
                winner_team=masters_teams[5],
                confirmed_by=organizer,
            ),
            get_or_create_match(
                db,
                tournament=masters,
                home_team=masters_teams[3],
                away_team=masters_teams[4],
                bracket_position=4,
                round_number=1,
                stage="Quarterfinal",
                status=MatchStatus.COMPLETED,
                scheduled_at=current_time - timedelta(days=1, hours=6),
                completed_at=current_time - timedelta(days=1, hours=4),
                home_score=0,
                away_score=2,
                winner_team=masters_teams[4],
                confirmed_by=organizer,
            ),
            get_or_create_match(
                db,
                tournament=masters,
                home_team=masters_teams[0],
                away_team=masters_teams[1],
                bracket_position=5,
                round_number=2,
                stage="Semifinal",
                status=MatchStatus.COMPLETED,
                scheduled_at=current_time - timedelta(hours=20),
                completed_at=current_time - timedelta(hours=18),
                home_score=2,
                away_score=1,
                winner_team=masters_teams[0],
                confirmed_by=organizer,
            ),
            get_or_create_match(
                db,
                tournament=masters,
                home_team=masters_teams[5],
                away_team=masters_teams[4],
                bracket_position=6,
                round_number=2,
                stage="Semifinal",
                status=MatchStatus.COMPLETED,
                scheduled_at=current_time - timedelta(hours=16),
                completed_at=current_time - timedelta(hours=14),
                home_score=1,
                away_score=2,
                winner_team=masters_teams[4],
                confirmed_by=organizer,
            ),
            get_or_create_match(
                db,
                tournament=masters,
                home_team=masters_teams[0],
                away_team=masters_teams[4],
                bracket_position=7,
                round_number=3,
                stage="Grand final",
                status=MatchStatus.SCHEDULED,
                scheduled_at=current_time + timedelta(hours=6),
            ),
        ]
    )

    invitational = get_or_create_tournament(
        db,
        name="Demo Spring Invitational",
        owner=organizer,
        status=TournamentStatus.COMPLETED,
        description=(
            "Completed event for reports, statistics and historical match views."
        ),
        max_teams=8,
        starts_at=current_time - timedelta(days=18),
        bracket_settings=create_bracket_settings(teams_count=8),
    )
    tournaments.append(invitational)
    invitational_teams = teams[4:12]
    approve_teams(
        db,
        tournament=invitational,
        teams=invitational_teams,
        decided_by=organizer,
    )

    completed_pairs = [
        (0, 7, 2, 0, 0),
        (1, 6, 1, 2, 6),
        (2, 5, 2, 1, 2),
        (3, 4, 2, 0, 3),
        (0, 6, 2, 1, 0),
        (2, 3, 0, 2, 3),
        (0, 3, 3, 2, 0),
    ]
    stages = [
        "Quarterfinal",
        "Quarterfinal",
        "Quarterfinal",
        "Quarterfinal",
        "Semifinal",
        "Semifinal",
        "Grand final",
    ]
    round_numbers = [1, 1, 1, 1, 2, 2, 3]
    for position, (home, away, home_score, away_score, winner) in enumerate(
        completed_pairs,
        start=1,
    ):
        matches.append(
            get_or_create_match(
                db,
                tournament=invitational,
                home_team=invitational_teams[home],
                away_team=invitational_teams[away],
                bracket_position=position,
                round_number=round_numbers[position - 1],
                stage=stages[position - 1],
                status=MatchStatus.COMPLETED,
                scheduled_at=current_time - timedelta(days=18 - position),
                completed_at=current_time - timedelta(days=18 - position, hours=-2),
                home_score=home_score,
                away_score=away_score,
                winner_team=invitational_teams[winner],
                confirmed_by=organizer,
            )
        )

    open_league = get_or_create_tournament(
        db,
        name="Demo Open League",
        owner=league_ops,
        status=TournamentStatus.REGISTRATION_OPEN,
        description=(
            "Open registration event with approved, pending and rejected teams."
        ),
        max_teams=16,
        starts_at=current_time + timedelta(days=5),
        format_="league",
        rules="Round robin groups, then playoffs for top four teams.",
        bracket_settings=create_bracket_settings(
            teams_count=16,
            bracket_type="round_robin_groups",
        ),
    )
    tournaments.append(open_league)
    for team in teams[:6]:
        ensure_participant(
            db,
            tournament=open_league,
            team=team,
            status=TournamentParticipantStatus.APPROVED,
            decided_by=league_ops,
        )
    for team in teams[6:10]:
        ensure_participant(
            db,
            tournament=open_league,
            team=team,
            status=TournamentParticipantStatus.PENDING,
        )
    for team in teams[10:12]:
        ensure_participant(
            db,
            tournament=open_league,
            team=team,
            status=TournamentParticipantStatus.REJECTED,
            decided_by=league_ops,
        )

    academy = get_or_create_tournament(
        db,
        name="Demo Academy Cup",
        owner=league_ops,
        status=TournamentStatus.REGISTRATION_CLOSED,
        description="Closed registration event with a ready opening schedule.",
        max_teams=8,
        starts_at=current_time + timedelta(days=1),
        discipline="Valorant",
        bracket_settings=create_bracket_settings(teams_count=8),
    )
    tournaments.append(academy)
    academy_teams = teams[2:10]
    approve_teams(db, tournament=academy, teams=academy_teams, decided_by=league_ops)
    for position in range(4):
        matches.append(
            get_or_create_match(
                db,
                tournament=academy,
                home_team=academy_teams[position],
                away_team=academy_teams[-(position + 1)],
                bracket_position=position + 1,
                round_number=1,
                stage="Opening round",
                status=MatchStatus.SCHEDULED,
                scheduled_at=current_time + timedelta(days=1, hours=position * 2),
            )
        )

    draft = get_or_create_tournament(
        db,
        name="Demo Draft Scrim Night",
        owner=organizer,
        status=TournamentStatus.DRAFT,
        description="Draft event for edit screens before registration opens.",
        max_teams=6,
        starts_at=current_time + timedelta(days=12),
        discipline="Dota 2",
        format_="swiss",
        rules="Swiss stage with manual pairings.",
        bracket_settings=create_bracket_settings(
            teams_count=6,
            bracket_type="swiss",
        ),
    )
    tournaments.append(draft)

    cancelled = get_or_create_tournament(
        db,
        name="Demo Cancelled Qualifier",
        owner=league_ops,
        status=TournamentStatus.CANCELLED,
        description="Cancelled event for edge-case status and admin exports.",
        max_teams=4,
        starts_at=current_time - timedelta(days=5),
        discipline="Apex Legends",
        bracket_settings=create_bracket_settings(teams_count=4),
    )
    tournaments.append(cancelled)
    cancelled_teams = teams[8:12]
    approve_teams(
        db,
        tournament=cancelled,
        teams=cancelled_teams,
        decided_by=league_ops,
    )
    matches.append(
        get_or_create_match(
            db,
            tournament=cancelled,
            home_team=cancelled_teams[0],
            away_team=cancelled_teams[1],
            bracket_position=1,
            round_number=1,
            stage="Cancelled semifinal",
            status=MatchStatus.CANCELLED,
            scheduled_at=current_time - timedelta(days=5, hours=-1),
        )
    )

    return tournaments, matches


def create_demo_ranked_matches(db: Session, players: list[User]) -> list[RankedMatch]:
    current_time = now_utc()
    ranked_matches: list[RankedMatch] = []

    for index in range(18):
        player_one = players[index]
        player_two = players[-(index + 1)]
        player_one_score = 13 + (index % 4)
        player_two_score = 8 + ((index * 3) % 6)
        winner = player_one if index % 3 != 1 else player_two
        if winner == player_two:
            player_one_score, player_two_score = player_two_score, player_one_score

        ranked_matches.append(
            get_or_create_ranked_match(
                db,
                player_one=player_one,
                player_two=player_two,
                status=RankedMatchStatus.COMPLETED,
                player_one_score=player_one_score,
                player_two_score=player_two_score,
                player_one_kills=player_one_score + 8 + (index % 5),
                player_one_deaths=player_two_score + 3 + (index % 3),
                player_one_assists=5 + (index % 7),
                player_two_kills=player_two_score + 6 + (index % 4),
                player_two_deaths=player_one_score + 4 + (index % 2),
                player_two_assists=4 + ((index + 2) % 6),
                winner=winner,
                completed_at=current_time - timedelta(days=index + 1),
            )
        )

    for index in range(4):
        match = get_or_create_ranked_match(
            db,
            player_one=players[20 + index * 2],
            player_two=players[21 + index * 2],
            status=RankedMatchStatus.SCHEDULED,
        )
        ranked_matches.append(match)
        ensure_matchmaking_request(
            db,
            user=players[20 + index * 2],
            status=MatchmakingRequestStatus.MATCHED,
            ranked_match=match,
        )
        ensure_matchmaking_request(
            db,
            user=players[21 + index * 2],
            status=MatchmakingRequestStatus.MATCHED,
            ranked_match=match,
        )

    for index in range(3):
        ranked_matches.append(
            get_or_create_ranked_match(
                db,
                player_one=players[32 + index * 2],
                player_two=players[33 + index * 2],
                status=RankedMatchStatus.CANCELLED,
            )
        )

    for player in players[42:46]:
        ensure_matchmaking_request(
            db,
            user=player,
            status=MatchmakingRequestStatus.SEARCHING,
        )

    return ranked_matches


def create_demo_disputes(
    db: Session,
    *,
    admin: User,
    moderator: User,
    players: list[User],
    matches: list[Match],
) -> list[MatchDispute]:
    completed_matches = [
        match for match in matches if match.status == MatchStatus.COMPLETED
    ]
    disputes = [
        ensure_dispute(
            db,
            match=completed_matches[1],
            opened_by=players[6],
            status=DisputeStatus.OPEN,
            reason="Opponent submitted a different screenshot for map two.",
        ),
        ensure_dispute(
            db,
            match=completed_matches[4],
            opened_by=players[12],
            status=DisputeStatus.RESOLVED,
            reason="Captain asked to verify overtime result.",
            resolved_by=admin,
            resolution="Reviewed scoreboard and confirmed the reported result.",
        ),
        ensure_dispute(
            db,
            match=completed_matches[8],
            opened_by=players[19],
            status=DisputeStatus.REJECTED,
            reason="Late roster substitution was reported after the match.",
            resolved_by=moderator,
            resolution="Rejected because the roster change was approved before start.",
        ),
    ]
    return disputes


def create_demo_notifications(
    db: Session,
    *,
    users: dict[str, User],
    players: list[User],
    tournaments: list[Tournament],
    matches: list[Match],
    ranked_matches: list[RankedMatch],
    disputes: list[MatchDispute],
) -> list[Notification]:
    notifications = [
        ensure_notification(
            db,
            user=players[0],
            title="Final match scheduled",
            message="Your CyberHub Masters final is scheduled for today.",
            related_entity_type="match",
            related_entity_id=matches[6].id,
        ),
        ensure_notification(
            db,
            user=players[4],
            title="Tournament application approved",
            message="Your team was approved for Demo Open League.",
            related_entity_type="tournament",
            related_entity_id=tournaments[2].id,
            is_read=True,
        ),
        ensure_notification(
            db,
            user=players[6],
            title="Dispute opened",
            message="Your score dispute is waiting for admin review.",
            related_entity_type="match_dispute",
            related_entity_id=disputes[0].id,
        ),
        ensure_notification(
            db,
            user=players[12],
            title="Dispute resolved",
            message="The moderation team confirmed your match result.",
            related_entity_type="match_dispute",
            related_entity_id=disputes[1].id,
            is_read=True,
        ),
        ensure_notification(
            db,
            user=players[20],
            title="Ranked match found",
            message="A ranked opponent is ready. Check your active match.",
            related_entity_type="ranked_match",
            related_entity_id=ranked_matches[18].id,
        ),
        ensure_notification(
            db,
            user=players[42],
            title="Searching for opponent",
            message="Matchmaking is active for your account.",
            related_entity_type="ranked_match",
            related_entity_id=None,
        ),
        ensure_notification(
            db,
            user=users["organizer"],
            title="New applications waiting",
            message="Demo Open League has pending team applications.",
            related_entity_type="tournament",
            related_entity_id=tournaments[2].id,
        ),
        ensure_notification(
            db,
            user=users["league_ops"],
            title="Opening round ready",
            message="Demo Academy Cup opening matches have been scheduled.",
            related_entity_type="tournament",
            related_entity_id=tournaments[3].id,
            is_read=True,
        ),
        ensure_notification(
            db,
            user=users["admin"],
            title="Open dispute",
            message="A demo dispute is waiting in the admin panel.",
            related_entity_type="match_dispute",
            related_entity_id=disputes[0].id,
        ),
        ensure_notification(
            db,
            user=users["moderator"],
            title="Report export sample",
            message="Demo data is ready for admin CSV export checks.",
            related_entity_type="tournament",
            related_entity_id=tournaments[1].id,
        ),
    ]
    return notifications


def create_demo_action_logs(
    db: Session,
    *,
    users: dict[str, User],
    tournaments: list[Tournament],
    matches: list[Match],
    ranked_matches: list[RankedMatch],
    disputes: list[MatchDispute],
) -> list[ActionLog]:
    logs = [
        ensure_action_log(
            db,
            actor=users["admin"],
            action="demo_admin_bootstrap",
            entity_type="user",
            entity_id=users["admin"].id,
            details={"role": UserRole.ADMIN.value},
        ),
        ensure_action_log(
            db,
            actor=users["organizer"],
            action="demo_tournament_created",
            entity_type="tournament",
            entity_id=tournaments[0].id,
            details={"status": tournaments[0].status.value, "teams": 8},
        ),
        ensure_action_log(
            db,
            actor=users["league_ops"],
            action="demo_tournament_registration_reviewed",
            entity_type="tournament",
            entity_id=tournaments[2].id,
            details={"approved": 6, "pending": 4, "rejected": 2},
        ),
        ensure_action_log(
            db,
            actor=users["organizer"],
            action="demo_match_result_confirmed",
            entity_type="match",
            entity_id=matches[0].id,
            details={"home_score": 2, "away_score": 0},
        ),
        ensure_action_log(
            db,
            actor=users["organizer"],
            action="demo_match_result_confirmed",
            entity_type="match",
            entity_id=matches[5].id,
            details={"home_score": 1, "away_score": 2},
        ),
        ensure_action_log(
            db,
            actor=users["admin"],
            action="demo_dispute_opened",
            entity_type="match_dispute",
            entity_id=disputes[0].id,
            details={"status": disputes[0].status.value},
        ),
        ensure_action_log(
            db,
            actor=users["admin"],
            action="demo_dispute_resolved",
            entity_type="match_dispute",
            entity_id=disputes[1].id,
            details={"status": disputes[1].status.value},
        ),
        ensure_action_log(
            db,
            actor=users["moderator"],
            action="demo_dispute_resolved",
            entity_type="match_dispute",
            entity_id=disputes[2].id,
            details={"status": disputes[2].status.value},
        ),
    ]

    for match in ranked_matches[:6]:
        actor = db.get(User, match.winner_id) if match.winner_id else None
        logs.append(
            ensure_action_log(
                db,
                actor=actor,
                action="demo_ranked_match_completed",
                entity_type="ranked_match",
                entity_id=match.id,
                details={"winner_id": match.winner_id},
            )
        )

    return logs


def seed_demo_data(db: Session, *, purge_existing: bool = True) -> dict[str, int]:
    summary: dict[str, int] = {}
    if purge_existing:
        summary.update(purge_demo_data(db))

    users, players = create_demo_users(db)
    teams = create_demo_teams(db, players)
    tournaments, matches = create_demo_tournaments(
        db,
        organizer=users["organizer"],
        league_ops=users["league_ops"],
        teams=teams,
    )
    ranked_matches = create_demo_ranked_matches(db, players)
    disputes = create_demo_disputes(
        db,
        admin=users["admin"],
        moderator=users["moderator"],
        players=players,
        matches=matches,
    )
    notifications = create_demo_notifications(
        db,
        users=users,
        players=players,
        tournaments=tournaments,
        matches=matches,
        ranked_matches=ranked_matches,
        disputes=disputes,
    )
    logs = create_demo_action_logs(
        db,
        users=users,
        tournaments=tournaments,
        matches=matches,
        ranked_matches=ranked_matches,
        disputes=disputes,
    )

    db.commit()

    created_user_ids = {user.id for user in users.values()} | {
        player.id for player in players
    }
    summary.update(
        {
            "users": len(created_user_ids),
            "teams": len(teams),
            "team_members": len(teams) * DEMO_TEAM_SIZE,
            "tournaments": len(tournaments),
            "matches": len(matches),
            "ranked_matches": len(ranked_matches),
            "matchmaking_requests": 12,
            "notifications": len(notifications),
            "disputes": len(disputes),
            "action_logs": len(logs),
        }
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed CyberHub demo data.")
    parser.add_argument(
        "--create-tables",
        action="store_true",
        help=(
            "Create tables before seeding. "
            "Use migrations for normal PostgreSQL setup."
        ),
    )
    parser.add_argument(
        "--keep-existing",
        action="store_true",
        help="Do not purge existing demo records before seeding.",
    )
    args = parser.parse_args()

    if args.create_tables:
        Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        summary = seed_demo_data(db, purge_existing=not args.keep_existing)

    print("CyberHub demo data is ready.")
    print(f"Demo password for all demo users: {DEMO_PASSWORD}")
    for key, value in summary.items():
        print(f"{key}: {value}")
    print("Useful logins:")
    print(f"admin{DEMO_EMAIL_SUFFIX}")
    print(f"moderator{DEMO_EMAIL_SUFFIX}")
    print(f"organizer{DEMO_EMAIL_SUFFIX}")
    print(f"league.ops{DEMO_EMAIL_SUFFIX}")
    print(f"player{DEMO_EMAIL_SUFFIX}")
    print(f"rival{DEMO_EMAIL_SUFFIX}")
    print(f"player01{DEMO_EMAIL_SUFFIX}")


if __name__ == "__main__":
    main()
