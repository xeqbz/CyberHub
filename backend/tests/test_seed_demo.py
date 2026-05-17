from sqlalchemy import func, select

from app.modules.matches.model import Match
from app.modules.platform.model import MatchDispute, Notification, RankedMatch
from app.modules.teams.model import Team
from app.modules.tournaments.model import Tournament
from app.modules.users.model import User
from app.scripts.seed_demo import seed_demo_data


def test_seed_demo_data_creates_full_demo_flow(test_session_factory):
    db = test_session_factory()
    try:
        summary = seed_demo_data(db)

        assert summary == {
            "users": 6,
            "teams": 4,
            "tournaments": 2,
            "matches": 2,
            "ranked_matches": 2,
            "notifications": 4,
            "disputes": 1,
        }
        assert db.scalar(select(func.count(User.id))) == 6
        assert db.scalar(select(func.count(Team.id))) == 4
        assert db.scalar(select(func.count(Tournament.id))) == 2
        assert db.scalar(select(func.count(Match.id))) == 2
        assert db.scalar(select(func.count(RankedMatch.id))) == 2
        assert db.scalar(select(func.count(Notification.id))) == 4
        assert db.scalar(select(func.count(MatchDispute.id))) == 1
    finally:
        db.close()


def test_seed_demo_data_is_idempotent(test_session_factory):
    db = test_session_factory()
    try:
        seed_demo_data(db)
        seed_demo_data(db)

        assert db.scalar(select(func.count(User.id))) == 6
        assert db.scalar(select(func.count(Team.id))) == 4
        assert db.scalar(select(func.count(Tournament.id))) == 2
        assert db.scalar(select(func.count(Match.id))) == 2
        assert db.scalar(select(func.count(RankedMatch.id))) == 2
        assert db.scalar(select(func.count(Notification.id))) == 4
        assert db.scalar(select(func.count(MatchDispute.id))) == 1
    finally:
        db.close()
