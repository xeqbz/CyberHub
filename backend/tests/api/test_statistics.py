from tests.api.helpers import (
    auth_headers,
    complete_match,
    create_ranked_match,
    prepare_match_context,
    register_user,
    submit_ranked_result,
)


def test_player_statistics_update_after_ranked_match(client):
    first = register_user(client, "alpha", "alpha@example.com")
    second = register_user(client, "bravo", "bravo@example.com")
    match = create_ranked_match(client, first, second)

    submit_ranked_result(client, first["access_token"], match["id"], 2, 0)

    response = client.get(
        "/api/v1/users/me",
        headers=auth_headers(first["access_token"]),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["wins"] == 1
    assert data["losses"] == 0
    assert data["rating"] > 1000


def test_team_statistics_aggregate_completed_matches(client):
    context = prepare_match_context(client)
    complete_match(
        client,
        context["owner"]["access_token"],
        context["match"]["id"],
        context["home_team"]["id"],
    )

    response = client.get("/api/v1/statistics/teams")

    assert response.status_code == 200
    stats = {item["name"]: item for item in response.json()}
    assert stats["Cyber Wolves"]["matches"] == 1
    assert stats["Cyber Wolves"]["wins"] == 1
    assert stats["Night Owls"]["losses"] == 1


def test_tournament_statistics_include_participants_and_matches(client):
    context = prepare_match_context(client)
    complete_match(
        client,
        context["owner"]["access_token"],
        context["match"]["id"],
        context["home_team"]["id"],
    )

    response = client.get("/api/v1/statistics/tournaments")

    assert response.status_code == 200
    tournament = response.json()[0]
    assert tournament["name"] == "Cyber Cup"
    assert tournament["participants"] == 2
    assert tournament["matches"] == 1
    assert tournament["completed_matches"] == 1


def test_statistics_overview_handles_missing_data(client):
    response = client.get("/api/v1/statistics/overview")

    assert response.status_code == 200
    assert response.json() == {
        "users": 0,
        "teams": 0,
        "tournaments": 0,
        "tournament_matches": 0,
        "ranked_matches": 0,
        "open_disputes": 0,
        "completed_matches": 0,
    }


def test_rankings_sort_players_by_rating(client):
    winner = register_user(client, "winner", "winner@example.com")
    loser = register_user(client, "loser", "loser@example.com")
    match = create_ranked_match(client, winner, loser)
    submit_ranked_result(client, winner["access_token"], match["id"], 2, 0)

    response = client.get("/api/v1/rankings")

    assert response.status_code == 200
    rankings = response.json()
    assert [item["username"] for item in rankings] == ["winner", "loser"]
