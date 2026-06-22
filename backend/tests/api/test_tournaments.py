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
    tournament_format: str = "single_elimination",
    discipline: str = "CS2",
) -> dict:
    response = client.post(
        "/api/v1/tournaments",
        json={
            "name": name,
            "description": "Main tournament",
            "status": status,
            "format": tournament_format,
            "discipline": discipline,
            "max_teams": 8,
            "starts_at": None,
        },
        headers=auth_headers(access_token),
    )
    assert response.status_code == 201
    return response.json()


def create_registered_teams(
    client,
    access_token: str,
    tournament_id: int,
    count: int,
) -> list[dict]:
    teams = []
    for index in range(count):
        team = create_team(client, access_token, name=f"Cyber Wolves {index + 1}")
        response = client.post(
            f"/api/v1/tournaments/{tournament_id}/participants",
            json={"team_id": team["id"]},
            headers=auth_headers(access_token),
        )
        assert response.status_code == 201
        teams.append(team)
    return teams


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


def test_list_tournaments_supports_server_filters(client):
    first_owner = register_user(client, "vadim", "vadim@example.com")
    second_owner = register_user(client, "alex", "alex@example.com")

    create_tournament(
        client,
        first_owner["access_token"],
        name="Cyber Cup",
        status="REGISTRATION_OPEN",
        tournament_format="single_elimination",
        discipline="CS2",
    )
    create_tournament(
        client,
        second_owner["access_token"],
        name="Dota Invitational",
        status="COMPLETED",
        tournament_format="round_robin",
        discipline="Dota 2",
    )

    response = client.get(
        "/api/v1/tournaments"
        "?search=dota&status=COMPLETED&discipline=dota&format=round_robin"
    )

    assert response.status_code == 200
    data = response.json()
    assert [item["name"] for item in data] == ["Dota Invitational"]


def test_list_tournaments_supports_scope_and_owner_filters(client):
    first_owner = register_user(client, "vadim", "vadim@example.com")
    second_owner = register_user(client, "alex", "alex@example.com")

    mine = create_tournament(
        client,
        first_owner["access_token"],
        name="My Open Cup",
        status="REGISTRATION_OPEN",
    )
    create_tournament(
        client,
        second_owner["access_token"],
        name="Other Open Cup",
        status="REGISTRATION_OPEN",
    )
    create_tournament(
        client,
        first_owner["access_token"],
        name="Archived Cup",
        status="COMPLETED",
    )

    response = client.get(
        f"/api/v1/tournaments?scope=ACTIVE&owner_id={mine['owner_id']}"
    )

    assert response.status_code == 200
    assert [item["name"] for item in response.json()] == ["My Open Cup"]


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


def test_owner_can_generate_single_elimination_bracket(client):
    owner = register_user(client, "vadim", "vadim@example.com")
    tournament = create_tournament(
        client,
        owner["access_token"],
        name="Cyber Cup",
        status="REGISTRATION_OPEN",
    )
    teams = create_registered_teams(
        client,
        owner["access_token"],
        tournament["id"],
        count=4,
    )

    status_response = client.patch(
        f"/api/v1/tournaments/{tournament['id']}",
        json={"status": "REGISTRATION_CLOSED"},
        headers=auth_headers(owner["access_token"]),
    )
    assert status_response.status_code == 200

    response = client.post(
        f"/api/v1/tournaments/{tournament['id']}/bracket/generate",
        headers=auth_headers(owner["access_token"]),
    )

    assert response.status_code == 201
    matches = response.json()
    assert len(matches) == 2
    assert {match["stage"] for match in matches} == {"Main bracket"}
    assert {match["round_number"] for match in matches} == {1}
    assert [match["bracket_position"] for match in matches] == [1, 2]
    assert {match["status"] for match in matches} == {"SCHEDULED"}

    generated_team_ids = [
        team_id
        for match in matches
        for team_id in (match["home_team_id"], match["away_team_id"])
    ]
    assert sorted(generated_team_ids) == sorted(team["id"] for team in teams)


def test_generate_round_robin_bracket_creates_all_pairings(client):
    owner = register_user(client, "vadim", "vadim@example.com")
    tournament = create_tournament(
        client,
        owner["access_token"],
        name="Cyber Round Robin",
        status="REGISTRATION_OPEN",
        tournament_format="round_robin",
    )
    teams = create_registered_teams(
        client,
        owner["access_token"],
        tournament["id"],
        count=3,
    )

    status_response = client.patch(
        f"/api/v1/tournaments/{tournament['id']}",
        json={"status": "REGISTRATION_CLOSED"},
        headers=auth_headers(owner["access_token"]),
    )
    assert status_response.status_code == 200

    response = client.post(
        f"/api/v1/tournaments/{tournament['id']}/bracket/generate",
        headers=auth_headers(owner["access_token"]),
    )

    assert response.status_code == 201
    matches = response.json()
    assert len(matches) == 3
    assert {match["stage"] for match in matches} == {"Round robin"}

    generated_pairs = {
        tuple(sorted((match["home_team_id"], match["away_team_id"])))
        for match in matches
    }
    expected_pairs = {
        tuple(sorted((first["id"], second["id"])))
        for index, first in enumerate(teams)
        for second in teams[index + 1 :]
    }
    assert generated_pairs == expected_pairs
    assert {match["round_number"] for match in matches} == {1, 2, 3}


def test_generate_double_elimination_bracket_creates_upper_opening_round(client):
    owner = register_user(client, "vadim", "vadim@example.com")
    tournament = create_tournament(
        client,
        owner["access_token"],
        name="Cyber Double",
        status="REGISTRATION_OPEN",
        tournament_format="double_elimination",
    )
    teams = create_registered_teams(
        client,
        owner["access_token"],
        tournament["id"],
        count=4,
    )

    status_response = client.patch(
        f"/api/v1/tournaments/{tournament['id']}",
        json={"status": "REGISTRATION_CLOSED"},
        headers=auth_headers(owner["access_token"]),
    )
    assert status_response.status_code == 200

    response = client.post(
        f"/api/v1/tournaments/{tournament['id']}/bracket/generate",
        headers=auth_headers(owner["access_token"]),
    )

    assert response.status_code == 201
    matches = response.json()
    assert len(matches) == 2
    assert {match["stage"] for match in matches} == {"Upper bracket"}
    assert {match["round_number"] for match in matches} == {1}

    generated_team_ids = [
        team_id
        for match in matches
        for team_id in (match["home_team_id"], match["away_team_id"])
    ]
    assert sorted(generated_team_ids) == sorted(team["id"] for team in teams)


def test_generate_swiss_bracket_creates_first_round(client):
    owner = register_user(client, "vadim", "vadim@example.com")
    tournament = create_tournament(
        client,
        owner["access_token"],
        name="Cyber Swiss",
        status="REGISTRATION_OPEN",
        tournament_format="swiss",
    )
    teams = create_registered_teams(
        client,
        owner["access_token"],
        tournament["id"],
        count=4,
    )

    status_response = client.patch(
        f"/api/v1/tournaments/{tournament['id']}",
        json={"status": "REGISTRATION_CLOSED"},
        headers=auth_headers(owner["access_token"]),
    )
    assert status_response.status_code == 200

    response = client.post(
        f"/api/v1/tournaments/{tournament['id']}/bracket/generate",
        headers=auth_headers(owner["access_token"]),
    )

    assert response.status_code == 201
    matches = response.json()
    assert len(matches) == 2
    assert {match["stage"] for match in matches} == {"Swiss"}
    assert {match["round_number"] for match in matches} == {1}

    generated_team_ids = [
        team_id
        for match in matches
        for team_id in (match["home_team_id"], match["away_team_id"])
    ]
    assert sorted(generated_team_ids) == sorted(team["id"] for team in teams)


def test_cannot_generate_bracket_before_registration_is_closed(client):
    owner = register_user(client, "vadim", "vadim@example.com")
    tournament = create_tournament(
        client,
        owner["access_token"],
        name="Cyber Cup",
        status="REGISTRATION_OPEN",
    )
    create_registered_teams(
        client,
        owner["access_token"],
        tournament["id"],
        count=2,
    )

    response = client.post(
        f"/api/v1/tournaments/{tournament['id']}/bracket/generate",
        headers=auth_headers(owner["access_token"]),
    )

    assert response.status_code == 409
    assert (
        response.json()["detail"]
        == "Close registration before generating the bracket"
    )


def test_cannot_generate_bracket_twice(client):
    owner = register_user(client, "vadim", "vadim@example.com")
    tournament = create_tournament(
        client,
        owner["access_token"],
        name="Cyber Cup",
        status="REGISTRATION_OPEN",
    )
    create_registered_teams(
        client,
        owner["access_token"],
        tournament["id"],
        count=2,
    )

    status_response = client.patch(
        f"/api/v1/tournaments/{tournament['id']}",
        json={"status": "REGISTRATION_CLOSED"},
        headers=auth_headers(owner["access_token"]),
    )
    assert status_response.status_code == 200

    first_response = client.post(
        f"/api/v1/tournaments/{tournament['id']}/bracket/generate",
        headers=auth_headers(owner["access_token"]),
    )
    second_response = client.post(
        f"/api/v1/tournaments/{tournament['id']}/bracket/generate",
        headers=auth_headers(owner["access_token"]),
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert (
        second_response.json()["detail"]
        == "Tournament already has generated or manually created matches"
    )
