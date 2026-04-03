def register_user(client, username: str, email: str, password: str = "strongpass123") -> dict:
    response = client.post(
        "/auth/register",
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


def create_team(client, access_token: str, name: str) -> dict:
    response = client.post(
        "/teams",
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
        "/tournaments",
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


def register_team_to_tournament(client, access_token: str, tournament_id: int, team_id: int) -> dict:
    response = client.post(
        f"/tournaments/{tournament_id}/participants",
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
        "/matches",
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


def prepare_match_context(client):
    tournament_owner = register_user(client, "owner", "owner@example.com")
    second_owner = register_user(client, "alex", "alex@example.com")

    home_team = create_team(client, tournament_owner["access_token"], "Cyber Wolves")
    away_team = create_team(client, second_owner["access_token"], "Night Owls")

    tournament = create_tournament(
        client,
        tournament_owner["access_token"],
        name="Cyber Cup",
        status="REGISTRATION_OPEN",
    )

    register_team_to_tournament(
        client,
        tournament_owner["access_token"],
        tournament["id"],
        home_team["id"],
    )
    register_team_to_tournament(
        client,
        tournament_owner["access_token"],
        tournament["id"],
        away_team["id"],
    )

    return tournament_owner, second_owner, tournament, home_team, away_team


def test_create_match_requires_auth(client):
    owner, _, tournament, home_team, away_team = prepare_match_context(client)

    response = client.post(
        "/matches",
        json={
            "tournament_id": tournament["id"],
            "home_team_id": home_team["id"],
            "away_team_id": away_team["id"],
            "scheduled_at": None,
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication credentials were not provided"


def test_create_match_returns_created_match(client):
    owner, _, tournament, home_team, away_team = prepare_match_context(client)

    response = client.post(
        "/matches",
        json={
            "tournament_id": tournament["id"],
            "home_team_id": home_team["id"],
            "away_team_id": away_team["id"],
            "scheduled_at": None,
        },
        headers=auth_headers(owner["access_token"]),
    )

    assert response.status_code == 201
    data = response.json()

    assert data["tournament_id"] == tournament["id"]
    assert data["home_team_id"] == home_team["id"]
    assert data["away_team_id"] == away_team["id"]
    assert data["status"] == "SCHEDULED"
    assert data["home_score"] is None
    assert data["away_score"] is None
    assert data["winner_team_id"] is None
    assert data["home_team"]["name"] == "Cyber Wolves"
    assert data["away_team"]["name"] == "Night Owls"


def test_non_owner_cannot_create_match(client):
    owner, second_owner, tournament, home_team, away_team = prepare_match_context(client)

    response = client.post(
        "/matches",
        json={
            "tournament_id": tournament["id"],
            "home_team_id": home_team["id"],
            "away_team_id": away_team["id"],
            "scheduled_at": None,
        },
        headers=auth_headers(second_owner["access_token"]),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Only tournament owner can perform this action"


def test_cannot_create_match_with_same_teams(client):
    owner, _, tournament, home_team, _ = prepare_match_context(client)

    response = client.post(
        "/matches",
        json={
            "tournament_id": tournament["id"],
            "home_team_id": home_team["id"],
            "away_team_id": home_team["id"],
            "scheduled_at": None,
        },
        headers=auth_headers(owner["access_token"]),
    )

    assert response.status_code == 422


def test_cannot_create_match_if_team_not_in_tournament(client):
    owner = register_user(client, "owner", "owner@example.com")
    other_user = register_user(client, "alex", "alex@example.com")
    outsider = register_user(client, "john", "john@example.com")

    home_team = create_team(client, owner["access_token"], "Cyber Wolves")
    away_team = create_team(client, other_user["access_token"], "Night Owls")
    outsider_team = create_team(client, outsider["access_token"], "Solo Team")

    tournament = create_tournament(
        client,
        owner["access_token"],
        name="Cyber Cup",
        status="REGISTRATION_OPEN",
    )

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

    response = client.post(
        "/matches",
        json={
            "tournament_id": tournament["id"],
            "home_team_id": home_team["id"],
            "away_team_id": outsider_team["id"],
            "scheduled_at": None,
        },
        headers=auth_headers(owner["access_token"]),
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Team is not registered in this tournament"


def test_update_match_score_completes_match(client):
    owner, _, tournament, home_team, away_team = prepare_match_context(client)
    match = create_match(
        client,
        owner["access_token"],
        tournament["id"],
        home_team["id"],
        away_team["id"],
    )

    response = client.patch(
        f"/matches/{match['id']}/score",
        json={
            "home_score": 2,
            "away_score": 1,
            "winner_team_id": home_team["id"],
        },
        headers=auth_headers(owner["access_token"]),
    )

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "COMPLETED"
    assert data["home_score"] == 2
    assert data["away_score"] == 1
    assert data["winner_team_id"] == home_team["id"]
    assert data["winner_team"]["name"] == "Cyber Wolves"


def test_invalid_winner_for_score_returns_409(client):
    owner, _, tournament, home_team, away_team = prepare_match_context(client)
    match = create_match(
        client,
        owner["access_token"],
        tournament["id"],
        home_team["id"],
        away_team["id"],
    )

    response = client.patch(
        f"/matches/{match['id']}/score",
        json={
            "home_score": 2,
            "away_score": 1,
            "winner_team_id": away_team["id"],
        },
        headers=auth_headers(owner["access_token"]),
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "winner_team_id does not match the provided score"


def test_list_tournament_matches_returns_created_match(client):
    owner, _, tournament, home_team, away_team = prepare_match_context(client)
    match = create_match(
        client,
        owner["access_token"],
        tournament["id"],
        home_team["id"],
        away_team["id"],
    )

    response = client.get(f"/matches/tournament/{tournament['id']}")

    assert response.status_code == 200
    data = response.json()

    assert len(data) == 1
    assert data[0]["id"] == match["id"]
    assert data[0]["home_team"]["name"] == "Cyber Wolves"
    assert data[0]["away_team"]["name"] == "Night Owls"


def test_delete_match_by_owner_returns_204(client):
    owner, _, tournament, home_team, away_team = prepare_match_context(client)
    match = create_match(
        client,
        owner["access_token"],
        tournament["id"],
        home_team["id"],
        away_team["id"],
    )

    delete_response = client.delete(
        f"/matches/{match['id']}",
        headers=auth_headers(owner["access_token"]),
    )

    assert delete_response.status_code == 204

    get_response = client.get(f"/matches/{match['id']}")
    assert get_response.status_code == 404