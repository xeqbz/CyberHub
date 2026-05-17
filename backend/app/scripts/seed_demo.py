from __future__ import annotations

import argparse
from datetime import UTC, datetime, timedelta

from sqlalchemy import or_, select
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

DEMO_PASSWORD = "demo12345"


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
            hashed_password=hash_password(DEMO_PASSWORD),
        )
        db.add(user)

    user.username = username
    user.email = email
    user.role = role
    user.is_active = True
    user.rating = rating
    user.wins = wins
    user.losses = losses
    user.draws = draws
    db.flush()
    return user


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

    return team


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


def get_or_create_tournament(
    db: Session,
    *,
    name: str,
    owner: User,
    status: TournamentStatus,
    description: str,
    max_teams: int = 8,
) -> Tournament:
    tournament = db.scalar(select(Tournament).where(Tournament.name == name))
    if tournament is None:
        tournament = Tournament(name=name, owner_id=owner.id)
        db.add(tournament)

    tournament.description = description
    tournament.owner_id = owner.id
    tournament.status = status
    tournament.format = "single_elimination"
    tournament.discipline = "CS2"
    tournament.rules = "Best of 3, standard competitive rules."
    tournament.bracket_settings = {"third_place_match": True, "seeded": True}
    tournament.max_teams = max_teams
    tournament.starts_at = datetime.now(UTC) + timedelta(days=3)
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
    if status != TournamentParticipantStatus.PENDING:
        participant.decided_by_id = decided_by.id if decided_by else tournament.owner_id
        participant.decided_at = datetime.now(UTC)
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
    home_score: int | None = None,
    away_score: int | None = None,
    winner_team: Team | None = None,
    confirmed_by: User | None = None,
) -> Match:
    match = db.scalar(
        select(Match).where(
            Match.tournament_id == tournament.id,
            Match.home_team_id == home_team.id,
            Match.away_team_id == away_team.id,
            Match.bracket_position == bracket_position,
        )
    )
    if match is None:
        match = Match(
            tournament_id=tournament.id,
            home_team_id=home_team.id,
            away_team_id=away_team.id,
            bracket_position=bracket_position,
        )
        db.add(match)

    match.status = status
    match.stage = "Main bracket"
    match.round_number = 1
    match.scheduled_at = datetime.now(UTC) + timedelta(days=4, hours=bracket_position)
    match.home_score = home_score
    match.away_score = away_score
    match.winner_team_id = winner_team.id if winner_team else None
    match.result_confirmed_by_id = confirmed_by.id if confirmed_by else None
    match.completed_at = datetime.now(UTC) if status == MatchStatus.COMPLETED else None
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
    winner: User | None = None,
) -> RankedMatch:
    match = db.scalar(
        select(RankedMatch).where(
            RankedMatch.player_one_id == player_one.id,
            RankedMatch.player_two_id == player_two.id,
        )
    )
    if match is None:
        match = RankedMatch(
            player_one_id=player_one.id,
            player_two_id=player_two.id,
        )
        db.add(match)

    match.status = status
    match.player_one_score = player_one_score
    match.player_two_score = player_two_score
    match.winner_id = winner.id if winner else None
    match.completed_at = (
        datetime.now(UTC) if status == RankedMatchStatus.COMPLETED else None
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
    resolved_by: User,
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

    dispute.reason = "Demo dispute: team asks moderator to review the final score."
    dispute.status = DisputeStatus.RESOLVED
    dispute.resolution = "Reviewed demo evidence and confirmed the result."
    dispute.resolved_by_id = resolved_by.id
    dispute.resolved_at = datetime.now(UTC)
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


def seed_demo_data(db: Session) -> dict[str, int]:
    admin = get_or_create_user(
        db,
        username="demo_admin",
        email="admin@cyberhub-demo.com",
        role=UserRole.ADMIN,
        rating=1420,
        wins=9,
        losses=3,
        draws=1,
    )
    organizer = get_or_create_user(
        db,
        username="demo_organizer",
        email="organizer@cyberhub-demo.com",
        role=UserRole.ORGANIZER,
        rating=1180,
        wins=4,
        losses=5,
    )
    player_one = get_or_create_user(
        db,
        username="demo_player",
        email="player@cyberhub-demo.com",
        rating=1264,
        wins=7,
        losses=4,
        draws=1,
    )
    player_two = get_or_create_user(
        db,
        username="demo_rival",
        email="rival@cyberhub-demo.com",
        rating=1210,
        wins=6,
        losses=5,
    )
    player_three = get_or_create_user(
        db,
        username="demo_support",
        email="support@cyberhub-demo.com",
        rating=980,
        wins=2,
        losses=7,
    )
    player_four = get_or_create_user(
        db,
        username="demo_captain",
        email="captain@cyberhub-demo.com",
        rating=1330,
        wins=8,
        losses=2,
    )

    wolves = get_or_create_team(
        db,
        name="Demo Cyber Wolves",
        description="Demo team for tournament, match and roster screenshots.",
        owner=player_one,
        members=[player_three],
    )
    owls = get_or_create_team(
        db,
        name="Demo Night Owls",
        description="Second demo roster with a completed match result.",
        owner=player_two,
        members=[],
    )
    titans = get_or_create_team(
        db,
        name="Demo Neon Titans",
        description="Pending tournament applicant for review flow.",
        owner=player_four,
        members=[],
    )
    admins = get_or_create_team(
        db,
        name="Demo Admin Squad",
        description="Organizer-owned team for permissions checks.",
        owner=organizer,
        members=[admin],
    )

    cup = get_or_create_tournament(
        db,
        name="Demo CyberHub Cup",
        owner=organizer,
        status=TournamentStatus.IN_PROGRESS,
        description="Seeded tournament with participants, matches and results.",
    )
    league = get_or_create_tournament(
        db,
        name="Demo Open League",
        owner=organizer,
        status=TournamentStatus.REGISTRATION_OPEN,
        description="Open registration tournament for application screenshots.",
    )

    ensure_participant(
        db,
        tournament=cup,
        team=wolves,
        status=TournamentParticipantStatus.APPROVED,
        decided_by=organizer,
    )
    ensure_participant(
        db,
        tournament=cup,
        team=owls,
        status=TournamentParticipantStatus.APPROVED,
        decided_by=organizer,
    )
    ensure_participant(
        db,
        tournament=cup,
        team=admins,
        status=TournamentParticipantStatus.APPROVED,
        decided_by=organizer,
    )
    ensure_participant(
        db,
        tournament=league,
        team=titans,
        status=TournamentParticipantStatus.PENDING,
    )

    completed_match = get_or_create_match(
        db,
        tournament=cup,
        home_team=wolves,
        away_team=owls,
        bracket_position=1,
        status=MatchStatus.COMPLETED,
        home_score=2,
        away_score=1,
        winner_team=wolves,
        confirmed_by=organizer,
    )
    scheduled_match = get_or_create_match(
        db,
        tournament=cup,
        home_team=admins,
        away_team=wolves,
        bracket_position=2,
        status=MatchStatus.SCHEDULED,
    )

    ranked_match = get_or_create_ranked_match(
        db,
        player_one=player_one,
        player_two=player_two,
        status=RankedMatchStatus.COMPLETED,
        player_one_score=16,
        player_two_score=12,
        winner=player_one,
    )
    active_ranked_match = get_or_create_ranked_match(
        db,
        player_one=player_three,
        player_two=player_four,
        status=RankedMatchStatus.SCHEDULED,
    )

    ensure_matchmaking_request(
        db,
        user=player_three,
        status=MatchmakingRequestStatus.MATCHED,
        ranked_match=active_ranked_match,
    )
    ensure_matchmaking_request(
        db,
        user=player_four,
        status=MatchmakingRequestStatus.MATCHED,
        ranked_match=active_ranked_match,
    )

    dispute = ensure_dispute(
        db,
        match=completed_match,
        opened_by=player_two,
        resolved_by=admin,
    )

    ensure_notification(
        db,
        user=player_one,
        title="Match scheduled",
        message=f"Match #{scheduled_match.id} is ready in Demo CyberHub Cup.",
        related_entity_type="match",
        related_entity_id=scheduled_match.id,
    )
    ensure_notification(
        db,
        user=player_two,
        title="Dispute reviewed",
        message=f"Your dispute #{dispute.id} was resolved by moderator.",
        related_entity_type="match_dispute",
        related_entity_id=dispute.id,
    )
    ensure_notification(
        db,
        user=organizer,
        title="New tournament application",
        message="Demo Neon Titans applied to Demo Open League.",
        related_entity_type="tournament",
        related_entity_id=league.id,
    )
    ensure_notification(
        db,
        user=player_three,
        title="Ranked match found",
        message=f"Ranked match #{active_ranked_match.id} is ready.",
        related_entity_type="ranked_match",
        related_entity_id=active_ranked_match.id,
    )

    ensure_action_log(
        db,
        actor=organizer,
        action="tournament_created",
        entity_type="tournament",
        entity_id=cup.id,
        details={"seed": "demo"},
    )
    ensure_action_log(
        db,
        actor=organizer,
        action="match_result_updated",
        entity_type="match",
        entity_id=completed_match.id,
        details={"home_score": 2, "away_score": 1},
    )
    ensure_action_log(
        db,
        actor=admin,
        action="admin_dispute_resolved",
        entity_type="match_dispute",
        entity_id=dispute.id,
        details={"status": DisputeStatus.RESOLVED},
    )
    ensure_action_log(
        db,
        actor=player_one,
        action="ranked_match_completed",
        entity_type="ranked_match",
        entity_id=ranked_match.id,
        details={"winner_id": player_one.id},
    )

    db.commit()

    return {
        "users": 6,
        "teams": 4,
        "tournaments": 2,
        "matches": 2,
        "ranked_matches": 2,
        "notifications": 4,
        "disputes": 1,
    }


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
    args = parser.parse_args()

    if args.create_tables:
        Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        summary = seed_demo_data(db)

    print("CyberHub demo data is ready.")
    print(f"Demo password for all demo users: {DEMO_PASSWORD}")
    for key, value in summary.items():
        print(f"{key}: {value}")
    print("Useful logins:")
    print("admin@cyberhub-demo.com")
    print("organizer@cyberhub-demo.com")
    print("player@cyberhub-demo.com")
    print("rival@cyberhub-demo.com")


if __name__ == "__main__":
    main()
