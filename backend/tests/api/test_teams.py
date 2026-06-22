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


def test_create_team_requires_auth(client):
    response = client.post(
        "/api/v1/teams",
        json={
            "name": "Cyber Wolves",
            "description": "Competitive squad",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication credentials were not provided"


def test_create_team_returns_created_team(client):
    tokens = register_user(client, "vadim", "vadim@example.com")

    response = client.post(
        "/api/v1/teams",
        json={
            "name": "Cyber Wolves",
            "description": "Competitive squad",
        },
        headers=auth_headers(tokens["access_token"]),
    )

    assert response.status_code == 201
    data = response.json()

    assert data["name"] == "Cyber Wolves"
    assert data["description"] == "Competitive squad"
    assert data["owner"]["username"] == "vadim"
    assert data["owner"]["email"] == "vadim@example.com"
    assert len(data["members"]) == 1
    assert data["members"][0]["role"] == "OWNER"
    assert data["members"][0]["user"]["username"] == "vadim"


def test_create_team_with_duplicate_name_returns_409(client):
    first_user = register_user(client, "vadim", "vadim@example.com")
    second_user = register_user(client, "alex", "alex@example.com")

    first_response = client.post(
        "/api/v1/teams",
        json={
            "name": "Cyber Wolves",
            "description": "First team",
        },
        headers=auth_headers(first_user["access_token"]),
    )

    second_response = client.post(
        "/api/v1/teams",
        json={
            "name": "Cyber Wolves",
            "description": "Second team",
        },
        headers=auth_headers(second_user["access_token"]),
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json()["detail"] == "Team with this name already exists"


def test_list_teams_returns_created_teams(client):
    first_user = register_user(client, "vadim", "vadim@example.com")
    second_user = register_user(client, "alex", "alex@example.com")

    client.post(
        "/api/v1/teams",
        json={"name": "Cyber Wolves", "description": "Team one"},
        headers=auth_headers(first_user["access_token"]),
    )
    client.post(
        "/api/v1/teams",
        json={"name": "Night Owls", "description": "Team two"},
        headers=auth_headers(second_user["access_token"]),
    )

    response = client.get("/api/v1/teams")

    assert response.status_code == 200
    data = response.json()

    names = [item["name"] for item in data]
    assert "Cyber Wolves" in names
    assert "Night Owls" in names


def test_get_my_teams_returns_current_user_teams(client):
    user = register_user(client, "vadim", "vadim@example.com")

    client.post(
        "/api/v1/teams",
        json={
            "name": "Cyber Wolves",
            "description": "Competitive squad",
        },
        headers=auth_headers(user["access_token"]),
    )

    response = client.get(
        "/api/v1/teams/my",
        headers=auth_headers(user["access_token"]),
    )

    assert response.status_code == 200
    data = response.json()

    assert len(data) == 1
    assert data[0]["name"] == "Cyber Wolves"
    assert data[0]["owner"]["username"] == "vadim"


def test_update_team_by_owner_returns_updated_team(client):
    user = register_user(client, "vadim", "vadim@example.com")

    create_response = client.post(
        "/api/v1/teams",
        json={
            "name": "Cyber Wolves",
            "description": "Competitive squad",
        },
        headers=auth_headers(user["access_token"]),
    )
    team_id = create_response.json()["id"]

    update_response = client.patch(
        f"/api/v1/teams/{team_id}",
        json={
            "name": "Cyber Wolves Pro",
            "description": "Updated description",
        },
        headers=auth_headers(user["access_token"]),
    )

    assert update_response.status_code == 200
    data = update_response.json()

    assert data["name"] == "Cyber Wolves Pro"
    assert data["description"] == "Updated description"


def test_update_team_by_non_owner_returns_403(client):
    owner = register_user(client, "vadim", "vadim@example.com")
    other_user = register_user(client, "alex", "alex@example.com")

    create_response = client.post(
        "/api/v1/teams",
        json={
            "name": "Cyber Wolves",
            "description": "Competitive squad",
        },
        headers=auth_headers(owner["access_token"]),
    )
    team_id = create_response.json()["id"]

    update_response = client.patch(
        f"/api/v1/teams/{team_id}",
        json={
            "name": "Hacked Name",
        },
        headers=auth_headers(other_user["access_token"]),
    )

    assert update_response.status_code == 403
    assert update_response.json()["detail"] == "Only team owner can perform this action"


def test_delete_team_by_owner_returns_204(client):
    user = register_user(client, "vadim", "vadim@example.com")

    create_response = client.post(
        "/api/v1/teams",
        json={
            "name": "Cyber Wolves",
            "description": "Competitive squad",
        },
        headers=auth_headers(user["access_token"]),
    )
    team_id = create_response.json()["id"]

    delete_response = client.delete(
        f"/api/v1/teams/{team_id}",
        headers=auth_headers(user["access_token"]),
    )

    assert delete_response.status_code == 204

    get_response = client.get(f"/api/v1/teams/{team_id}")
    assert get_response.status_code == 404
