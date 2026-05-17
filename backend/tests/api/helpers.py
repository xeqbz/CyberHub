def register_user(
    client,
    username: str,
    email: str,
    password: str = "strongpass123",
) -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": username,
            "email": email,
            "password": password,
        },
    )
    assert response.status_code == 201
    return response.json()


def auth_headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


def bootstrap_admin(client, user_tokens: dict) -> dict:
    response = client.post(
        "/api/v1/admin/bootstrap",
        headers=auth_headers(user_tokens["access_token"]),
    )
    assert response.status_code == 200
    return response.json()


def create_team(client, access_token: str, name: str) -> dict:
    response = client.post(
        "/api/v1/teams",
        json={
            "name": name,
            "description": f"{name} description",
        },
        headers=auth_headers(access_token),
    )
    assert response.status_code == 201
    return response.json()


def create_tournament(
    client,
    access_token: str,
    name: str = "Cyber Cup",
    status: str = "REGISTRATION_OPEN",
) -> dict:
    response = client.post(
        "/api/v1/tournaments",
        json={
            "name": name,
            "description": "Main tournament",
            "status": status,
            "max_teams": 8,
            "starts_at": None,
        },
        headers=auth_headers(access_token),
    )
    assert response.status_code == 201
    return response.json()


def register_team_to_tournament(
    client,
    access_token: str,
    tournament_id: int,
    team_id: int,
) -> dict:
    response = client.post(
        f"/api/v1/tournaments/{tournament_id}/participants",
        json={"team_id": team_id},
        headers=auth_headers(access_token),
    )
    assert response.status_code == 201
    return response.json()


def create_match(
    client,
    access_token: str,
    tournament_id: int,
    home_team_id: int,
    away_team_id: int,
) -> dict:
    response = client.post(
        "/api/v1/matches",
        json={
            "tournament_id": tournament_id,
            "home_team_id": home_team_id,
            "away_team_id": away_team_id,
            "scheduled_at": None,
        },
        headers=auth_headers(access_token),
    )
    assert response.status_code == 201
    return response.json()


def complete_match(
    client,
    access_token: str,
    match_id: int,
    winner_team_id: int,
    home_score: int = 2,
    away_score: int = 1,
) -> dict:
    response = client.patch(
        f"/api/v1/matches/{match_id}/score",
        json={
            "home_score": home_score,
            "away_score": away_score,
            "winner_team_id": winner_team_id,
        },
        headers=auth_headers(access_token),
    )
    assert response.status_code == 200
    return response.json()


def prepare_match_context(client, same_owner: bool = False) -> dict:
    owner = register_user(client, "owner", "owner@example.com")
    away_owner = owner
    if not same_owner:
        away_owner = register_user(client, "away_owner", "away@example.com")

    home_team = create_team(client, owner["access_token"], "Cyber Wolves")
    away_team = create_team(client, away_owner["access_token"], "Night Owls")
    tournament = create_tournament(client, owner["access_token"])

    register_team_to_tournament(
        client,
        owner["access_token"],
        tournament["id"],
        home_team["id"],
    )
    register_team_to_tournament(
        client,
        owner["access_token"],
        tournament["id"],
        away_team["id"],
    )

    match = create_match(
        client,
        owner["access_token"],
        tournament["id"],
        home_team["id"],
        away_team["id"],
    )

    return {
        "owner": owner,
        "away_owner": away_owner,
        "tournament": tournament,
        "home_team": home_team,
        "away_team": away_team,
        "match": match,
    }


def create_ranked_match(client, first_tokens: dict, second_tokens: dict) -> dict:
    first_response = client.post(
        "/api/v1/ranked/matchmaking",
        headers=auth_headers(first_tokens["access_token"]),
    )
    assert first_response.status_code == 200
    assert first_response.json()["status"] == "SEARCHING"

    second_response = client.post(
        "/api/v1/ranked/matchmaking",
        headers=auth_headers(second_tokens["access_token"]),
    )
    assert second_response.status_code == 200
    data = second_response.json()
    assert data["status"] == "MATCHED"
    return data["match"]


def submit_ranked_result(
    client,
    access_token: str,
    match_id: int,
    player_one_score: int = 2,
    player_two_score: int = 1,
) -> dict:
    response = client.patch(
        f"/api/v1/ranked/matches/{match_id}/result",
        json={
            "player_one_score": player_one_score,
            "player_two_score": player_two_score,
        },
        headers=auth_headers(access_token),
    )
    assert response.status_code == 200
    return response.json()
