from sqlalchemy import func, select

from app.modules.matches.model import Match
from app.modules.platform.model import (
    ActionLog,
    MatchDispute,
    MatchmakingRequest,
    Notification,
    RankedMatch,
)
from app.modules.teams.model import Team
from app.modules.tournaments.model import Tournament
from app.modules.users.model import User
from app.scripts.seed_demo import seed_demo_data


def test_seed_demo_data_creates_full_demo_flow(test_session_factory):
    db = test_session_factory()
    try:
        summary = seed_demo_data(db)

        assert summary["users"] == 64
        assert summary["teams"] == 12
        assert summary["team_members"] == 60
        assert summary["tournaments"] == 6
        assert summary["matches"] == 19
        assert summary["ranked_matches"] == 25
        assert summary["matchmaking_requests"] == 12
        assert summary["notifications"] == 10
        assert summary["disputes"] == 3
        assert summary["action_logs"] == 14
        assert db.scalar(select(func.count(User.id))) == 64
        assert db.scalar(select(func.count(Team.id))) == 12
        assert db.scalar(select(func.count(Tournament.id))) == 6
        assert db.scalar(select(func.count(Match.id))) == 19
        assert db.scalar(select(func.count(RankedMatch.id))) == 25
        assert db.scalar(select(func.count(MatchmakingRequest.id))) == 12
        assert db.scalar(select(func.count(Notification.id))) == 10
        assert db.scalar(select(func.count(MatchDispute.id))) == 3
        assert db.scalar(select(func.count(ActionLog.id))) == 14

        completed_ranked_match = db.scalar(
            select(RankedMatch).where(RankedMatch.player_one_kills > 0)
        )
        assert completed_ranked_match is not None
        assert completed_ranked_match.player_one_kda > 0
    finally:
        db.close()


def test_seed_demo_data_is_idempotent(test_session_factory):
    db = test_session_factory()
    try:
        seed_demo_data(db)
        seed_demo_data(db)

        assert db.scalar(select(func.count(User.id))) == 64
        assert db.scalar(select(func.count(Team.id))) == 12
        assert db.scalar(select(func.count(Tournament.id))) == 6
        assert db.scalar(select(func.count(Match.id))) == 19
        assert db.scalar(select(func.count(RankedMatch.id))) == 25
        assert db.scalar(select(func.count(MatchmakingRequest.id))) == 12
        assert db.scalar(select(func.count(Notification.id))) == 10
        assert db.scalar(select(func.count(MatchDispute.id))) == 3
        assert db.scalar(select(func.count(ActionLog.id))) == 14
    finally:
        db.close()
