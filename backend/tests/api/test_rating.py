from app.modules.platform.api import _apply_elo
from app.modules.platform.model import MatchmakingRequest, RankedMatch
from app.modules.users.model import User
from tests.api.helpers import (
    auth_headers,
    create_ranked_match,
    register_user,
    submit_ranked_result,
)


def test_ranked_result_recalculates_player_ratings(client):
    first = register_user(client, "alpha", "alpha@example.com")
    second = register_user(client, "bravo", "bravo@example.com")
    match = create_ranked_match(client, first, second)

    result = submit_ranked_result(
        client,
        first["access_token"],
        match["id"],
        player_one_score=2,
        player_two_score=0,
    )

    assert result["status"] == "COMPLETED"
    assert result["winner_id"] == match["player_one_id"]

    first_profile = client.get(
        "/api/v1/users/me",
        headers=auth_headers(first["access_token"]),
    ).json()
    second_profile = client.get(
        "/api/v1/users/me",
        headers=auth_headers(second["access_token"]),
    ).json()

    assert first_profile["rating"] > 1000
    assert first_profile["wins"] == 1
    assert second_profile["rating"] < 1000
    assert second_profile["losses"] == 1


def test_ranked_result_stores_kda_statistics(client):
    first = register_user(client, "alpha", "alpha@example.com")
    second = register_user(client, "bravo", "bravo@example.com")
    match = create_ranked_match(client, first, second)

    result = submit_ranked_result(
        client,
        first["access_token"],
        match["id"],
        player_one_score=2,
        player_two_score=1,
        player_one_kills=24,
        player_one_deaths=8,
        player_one_assists=6,
        player_two_kills=18,
        player_two_deaths=15,
        player_two_assists=4,
    )

    assert result["player_one_kills"] == 24
    assert result["player_one_deaths"] == 8
    assert result["player_one_assists"] == 6
    assert result["player_one_kda"] == 3.75
    assert result["player_two_kda"] == 1.47


def test_ranked_rating_changes_after_sequential_matches(client):
    first = register_user(client, "alpha", "alpha@example.com")
    second = register_user(client, "bravo", "bravo@example.com")
    third = register_user(client, "charlie", "charlie@example.com")

    first_match = create_ranked_match(client, first, second)
    submit_ranked_result(client, first["access_token"], first_match["id"], 2, 0)
    after_first = client.get(
        "/api/v1/users/me",
        headers=auth_headers(first["access_token"]),
    ).json()

    second_match = create_ranked_match(client, first, third)
    submit_ranked_result(client, first["access_token"], second_match["id"], 2, 1)
    after_second = client.get(
        "/api/v1/users/me",
        headers=auth_headers(first["access_token"]),
    ).json()

    assert after_second["wins"] == 2
    assert after_second["rating"] > after_first["rating"]


def test_elo_handles_boundary_rating_values():
    low_rated = User(
        id=1,
        username="low",
        email="low@example.com",
        hashed_password="hash",
        rating=100,
        wins=0,
        losses=0,
        draws=0,
    )
    high_rated = User(
        id=2,
        username="high",
        email="high@example.com",
        hashed_password="hash",
        rating=3000,
        wins=0,
        losses=0,
        draws=0,
    )
    match = RankedMatch(
        player_one_id=1,
        player_two_id=2,
        winner_id=1,
        player_one=low_rated,
        player_two=high_rated,
    )

    _apply_elo(match)

    assert low_rated.rating > 100
    assert high_rated.rating < 3000
    assert low_rated.wins == 1
    assert high_rated.losses == 1


def test_rankings_reflect_updated_ratings(client):
    winner = register_user(client, "winner", "winner@example.com")
    loser = register_user(client, "loser", "loser@example.com")
    match = create_ranked_match(client, winner, loser)

    submit_ranked_result(client, winner["access_token"], match["id"], 2, 0)

    response = client.get("/api/v1/rankings")

    assert response.status_code == 200
    rankings = response.json()
    assert rankings[0]["username"] == "winner"
    assert rankings[0]["rating"] > rankings[1]["rating"]


def test_matchmaking_respects_discipline_and_mode(client):
    first = register_user(client, "alpha", "alpha@example.com")
    second = register_user(client, "bravo", "bravo@example.com")
    third = register_user(client, "charlie", "charlie@example.com")

    first_response = client.post(
        "/api/v1/ranked/matchmaking",
        json={"discipline": "CS2", "mode": "1v1"},
        headers=auth_headers(first["access_token"]),
    )
    second_response = client.post(
        "/api/v1/ranked/matchmaking",
        json={"discipline": "Dota 2", "mode": "1v1"},
        headers=auth_headers(second["access_token"]),
    )
    third_response = client.post(
        "/api/v1/ranked/matchmaking",
        json={"discipline": "CS2", "mode": "1v1"},
        headers=auth_headers(third["access_token"]),
    )

    assert first_response.status_code == 200
    assert first_response.json()["status"] == "SEARCHING"
    assert second_response.status_code == 200
    assert second_response.json()["status"] == "SEARCHING"
    assert third_response.status_code == 200
    assert third_response.json()["status"] == "MATCHED"
    assert third_response.json()["match"]["discipline"] == "CS2"
    assert third_response.json()["match"]["mode"] == "1v1"


def test_matchmaking_expands_rating_range_after_waiting(
    client,
    test_session_factory,
):
    from datetime import UTC, datetime, timedelta

    first = register_user(client, "alpha", "alpha@example.com")
    second = register_user(client, "bravo", "bravo@example.com")

    first_response = client.post(
        "/api/v1/ranked/matchmaking",
        json={"discipline": "CS2", "mode": "1v1"},
        headers=auth_headers(first["access_token"]),
    )
    assert first_response.status_code == 200
    assert first_response.json()["status"] == "SEARCHING"

    db = test_session_factory()
    try:
        first_profile = db.query(User).filter_by(username="alpha").one()
        second_profile = db.query(User).filter_by(username="bravo").one()
        first_profile.rating = 1000
        second_profile.rating = 1600
        request = db.query(MatchmakingRequest).filter_by(user_id=first_profile.id).one()
        request.created_at = datetime.now(UTC) - timedelta(minutes=45)
        db.add(first_profile)
        db.add(second_profile)
        db.add(request)
        db.commit()
    finally:
        db.close()

    second_response = client.post(
        "/api/v1/ranked/matchmaking",
        json={"discipline": "CS2", "mode": "1v1"},
        headers=auth_headers(second["access_token"]),
    )

    assert second_response.status_code == 200
    assert second_response.json()["status"] == "MATCHED"
    assert second_response.json()["rating_range"] >= 600
