def register_user(
    client, username: str, email: str, password: str = "strongpass123"
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


def create_team(client, access_token: str, name: str = "Cyber Wolves") -> dict:
    response = client.post(
        "/api/v1/teams",
        json={
            "name": name,
            "description": "Competitive squad",
        },
        headers=auth_headers(access_token),
    )
    assert response.status_code == 201
    return response.json()


def create_tournament(
    client,
    access_token: str,
    name: str = "Cyber Cup",
    status: str = "DRAFT",
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


def test_create_tournament_requires_auth(client):
    response = client.post(
        "/api/v1/tournaments",
        json={
            "name": "Cyber Cup",
            "description": "Main tournament",
            "status": "DRAFT",
            "max_teams": 8,
            "starts_at": None,
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication credentials were not provided"


def test_create_tournament_returns_created_tournament(client):
    owner = register_user(client, "vadim", "vadim@example.com")

    response = client.post(
        "/api/v1/tournaments",
        json={
            "name": "Cyber Cup",
            "description": "Main tournament",
            "status": "DRAFT",
            "max_teams": 8,
            "starts_at": None,
        },
        headers=auth_headers(owner["access_token"]),
    )

    assert response.status_code == 201
    data = response.json()

    assert data["name"] == "Cyber Cup"
    assert data["description"] == "Main tournament"
    assert data["status"] == "DRAFT"
    assert data["max_teams"] == 8
    assert data["owner"]["username"] == "vadim"
    assert data["participants"] == []


def test_create_tournament_with_duplicate_name_returns_409(client):
    first_owner = register_user(client, "vadim", "vadim@example.com")
    second_owner = register_user(client, "alex", "alex@example.com")

    first_response = client.post(
        "/api/v1/tournaments",
        json={
            "name": "Cyber Cup",
            "description": "Main tournament",
            "status": "DRAFT",
            "max_teams": 8,
            "starts_at": None,
        },
        headers=auth_headers(first_owner["access_token"]),
    )

    second_response = client.post(
        "/api/v1/tournaments",
        json={
            "name": "Cyber Cup",
            "description": "Another tournament",
            "status": "DRAFT",
            "max_teams": 16,
            "starts_at": None,
        },
        headers=auth_headers(second_owner["access_token"]),
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert (
        second_response.json()["detail"] == "Tournament with this name already exists"
    )


def test_list_tournaments_returns_created_tournaments(client):
    first_owner = register_user(client, "vadim", "vadim@example.com")
    second_owner = register_user(client, "alex", "alex@example.com")

    create_tournament(client, first_owner["access_token"], name="Cyber Cup")
    create_tournament(client, second_owner["access_token"], name="Night League")

    response = client.get("/api/v1/tournaments")

    assert response.status_code == 200
    data = response.json()

    names = [item["name"] for item in data]
    assert "Cyber Cup" in names
    assert "Night League" in names


def test_update_tournament_by_owner_returns_updated_tournament(client):
    owner = register_user(client, "vadim", "vadim@example.com")
    tournament = create_tournament(client, owner["access_token"], name="Cyber Cup")

    response = client.patch(
        f"/api/v1/tournaments/{tournament['id']}",
        json={
            "name": "Cyber Cup Pro",
            "description": "Updated description",
            "status": "REGISTRATION_OPEN",
            "max_teams": 16,
        },
        headers=auth_headers(owner["access_token"]),
    )

    assert response.status_code == 200
    data = response.json()

    assert data["name"] == "Cyber Cup Pro"
    assert data["description"] == "Updated description"
    assert data["status"] == "REGISTRATION_OPEN"
    assert data["max_teams"] == 16


def test_update_tournament_by_non_owner_returns_403(client):
    owner = register_user(client, "vadim", "vadim@example.com")
    other_user = register_user(client, "alex", "alex@example.com")
    tournament = create_tournament(client, owner["access_token"], name="Cyber Cup")

    response = client.patch(
        f"/api/v1/tournaments/{tournament['id']}",
        json={
            "name": "Hacked Cup",
        },
        headers=auth_headers(other_user["access_token"]),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Only tournament owner can perform this action"


def test_can_add_participant_when_registration_is_open(client):
    owner = register_user(client, "vadim", "vadim@example.com")
    team = create_team(client, owner["access_token"], name="Cyber Wolves")
    tournament = create_tournament(
        client,
        owner["access_token"],
        name="Cyber Cup",
        status="REGISTRATION_OPEN",
    )

    response = client.post(
        f"/api/v1/tournaments/{tournament['id']}/participants",
        json={
            "team_id": team["id"],
        },
        headers=auth_headers(owner["access_token"]),
    )

    assert response.status_code == 201
    data = response.json()

    assert data["tournament_id"] == tournament["id"]
    assert data["team_id"] == team["id"]
    assert data["team"]["name"] == "Cyber Wolves"


def test_cannot_add_participant_when_registration_is_closed(client):
    owner = register_user(client, "vadim", "vadim@example.com")
    team = create_team(client, owner["access_token"], name="Cyber Wolves")
    tournament = create_tournament(
        client,
        owner["access_token"],
        name="Cyber Cup",
        status="DRAFT",
    )

    response = client.post(
        f"/api/v1/tournaments/{tournament['id']}/participants",
        json={
            "team_id": team["id"],
        },
        headers=auth_headers(owner["access_token"]),
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Tournament registration is not open"


def test_cannot_add_same_team_twice_to_tournament(client):
    owner = register_user(client, "vadim", "vadim@example.com")
    team = create_team(client, owner["access_token"], name="Cyber Wolves")
    tournament = create_tournament(
        client,
        owner["access_token"],
        name="Cyber Cup",
        status="REGISTRATION_OPEN",
    )

    first_response = client.post(
        f"/api/v1/tournaments/{tournament['id']}/participants",
        json={"team_id": team["id"]},
        headers=auth_headers(owner["access_token"]),
    )

    second_response = client.post(
        f"/api/v1/tournaments/{tournament['id']}/participants",
        json={"team_id": team["id"]},
        headers=auth_headers(owner["access_token"]),
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert (
        second_response.json()["detail"]
        == "Team is already registered in this tournament"
    )


def test_can_remove_participant(client):
    owner = register_user(client, "vadim", "vadim@example.com")
    team = create_team(client, owner["access_token"], name="Cyber Wolves")
    tournament = create_tournament(
        client,
        owner["access_token"],
        name="Cyber Cup",
        status="REGISTRATION_OPEN",
    )

    add_response = client.post(
        f"/api/v1/tournaments/{tournament['id']}/participants",
        json={"team_id": team["id"]},
        headers=auth_headers(owner["access_token"]),
    )
    assert add_response.status_code == 201

    delete_response = client.delete(
        f"/api/v1/tournaments/{tournament['id']}/participants/{team['id']}",
        headers=auth_headers(owner["access_token"]),
    )
    assert delete_response.status_code == 204

    list_response = client.get(f"/api/v1/tournaments/{tournament['id']}/participants")
    assert list_response.status_code == 200
    assert list_response.json() == []
