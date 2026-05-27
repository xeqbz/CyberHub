from tests.api.helpers import (
    auth_headers,
    create_match,
    create_team,
    create_tournament,
    register_team_to_tournament,
    register_user,
)


def test_users_me_requires_auth(client):
    response = client.get("/api/v1/users/me")

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication credentials were not provided"


def test_users_me_returns_current_user(client):
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword",
        },
    )

    token = register_response.json()["access_token"]

    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert data["is_active"] is True
    assert data["role"] == "USER"


def test_profile_history_returns_user_participation(client):
    user = register_user(client, "alpha", "alpha@example.com")
    other = register_user(client, "bravo", "bravo@example.com")
    team = create_team(client, user["access_token"], "Alpha Team")
    other_team = create_team(client, other["access_token"], "Bravo Team")
    tournament = create_tournament(client, user["access_token"])
    register_team_to_tournament(
        client,
        user["access_token"],
        tournament["id"],
        team["id"],
    )
    register_team_to_tournament(
        client,
        user["access_token"],
        tournament["id"],
        other_team["id"],
    )
    create_match(
        client,
        user["access_token"],
        tournament["id"],
        team["id"],
        other_team["id"],
    )

    response = client.get(
        "/api/v1/profile/history",
        headers=auth_headers(user["access_token"]),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["teams"][0]["name"] == "Alpha Team"
    assert data["tournaments"][0]["name"] == tournament["name"]
    assert data["tournament_matches"][0]["home_team_name"] == "Alpha Team"
