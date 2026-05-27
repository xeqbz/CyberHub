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
    tournament_format: str = "single_elimination",
) -> dict:
    response = client.post(
        "/api/v1/tournaments",
        json={
            "name": name,
            "description": "Main tournament",
            "status": status,
            "format": tournament_format,
            "max_teams": 8,
            "starts_at": None,
        },
        headers=auth_headers(access_token),
    )
    assert response.status_code == 201
    return response.json()


def register_team_to_tournament(
    client, access_token: str, tournament_id: int, team_id: int
) -> dict:
    response = client.post(
        f"/api/v1/tournaments/{tournament_id}/participants",
        json={"team_id": team_id},
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
        team = create_team(client, access_token, f"Team {index + 1}")
        register_team_to_tournament(client, access_token, tournament_id, team["id"])
        teams.append(team)
    return teams


def close_registration(client, access_token: str, tournament_id: int) -> None:
    response = client.patch(
        f"/api/v1/tournaments/{tournament_id}",
        json={"status": "REGISTRATION_CLOSED"},
        headers=auth_headers(access_token),
    )
    assert response.status_code == 200


def generate_bracket(client, access_token: str, tournament_id: int) -> list[dict]:
    response = client.post(
        f"/api/v1/tournaments/{tournament_id}/bracket/generate",
        headers=auth_headers(access_token),
    )
    assert response.status_code == 201
    return response.json()


def complete_match(
    client,
    access_token: str,
    match: dict,
    winner_team_id: int,
) -> dict:
    loser_score = 1
    winner_score = 2
    response = client.patch(
        f"/api/v1/matches/{match['id']}/score",
        json={
            "home_score": winner_score
            if match["home_team_id"] == winner_team_id
            else loser_score,
            "away_score": winner_score
            if match["away_team_id"] == winner_team_id
            else loser_score,
            "winner_team_id": winner_team_id,
        },
        headers=auth_headers(access_token),
    )
    assert response.status_code == 200
    return response.json()


def list_tournament_matches(client, tournament_id: int) -> list[dict]:
    response = client.get(f"/api/v1/matches/tournament/{tournament_id}")
    assert response.status_code == 200
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
        "/api/v1/matches",
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
        "/api/v1/matches",
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
    owner, second_owner, tournament, home_team, away_team = prepare_match_context(
        client
    )

    response = client.post(
        "/api/v1/matches",
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
        "/api/v1/matches",
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
        "/api/v1/matches",
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
        f"/api/v1/matches/{match['id']}/score",
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
        f"/api/v1/matches/{match['id']}/score",
        json={
            "home_score": 2,
            "away_score": 1,
            "winner_team_id": away_team["id"],
        },
        headers=auth_headers(owner["access_token"]),
    )

    assert response.status_code == 409
    assert (
        response.json()["detail"] == "winner_team_id does not match the provided score"
    )


def test_list_tournament_matches_returns_created_match(client):
    owner, _, tournament, home_team, away_team = prepare_match_context(client)
    match = create_match(
        client,
        owner["access_token"],
        tournament["id"],
        home_team["id"],
        away_team["id"],
    )

    response = client.get(f"/api/v1/matches/tournament/{tournament['id']}")

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
        f"/api/v1/matches/{match['id']}",
        headers=auth_headers(owner["access_token"]),
    )

    assert delete_response.status_code == 204

    get_response = client.get(f"/api/v1/matches/{match['id']}")
    assert get_response.status_code == 404


def test_single_elimination_winners_advance_to_next_round(client):
    owner = register_user(client, "owner_se", "owner-se@example.com")
    tournament = create_tournament(
        client,
        owner["access_token"],
        name="Single Auto Cup",
        status="REGISTRATION_OPEN",
        tournament_format="single_elimination",
    )
    create_registered_teams(
        client,
        owner["access_token"],
        tournament["id"],
        count=4,
    )
    close_registration(client, owner["access_token"], tournament["id"])

    opening_matches = generate_bracket(
        client,
        owner["access_token"],
        tournament["id"],
    )
    winners = [match["home_team_id"] for match in opening_matches]

    for match, winner_team_id in zip(opening_matches, winners):
        complete_match(client, owner["access_token"], match, winner_team_id)

    matches = list_tournament_matches(client, tournament["id"])
    final_matches = [
        match
        for match in matches
        if match["stage"] == "Main bracket" and match["round_number"] == 2
    ]

    assert len(final_matches) == 1
    final_match = final_matches[0]
    assert {final_match["home_team_id"], final_match["away_team_id"]} == set(winners)


def test_double_elimination_auto_creates_lower_and_grand_final(client):
    owner = register_user(client, "owner_de", "owner-de@example.com")
    tournament = create_tournament(
        client,
        owner["access_token"],
        name="Double Auto Cup",
        status="REGISTRATION_OPEN",
        tournament_format="double_elimination",
    )
    create_registered_teams(
        client,
        owner["access_token"],
        tournament["id"],
        count=4,
    )
    close_registration(client, owner["access_token"], tournament["id"])

    opening_matches = generate_bracket(
        client,
        owner["access_token"],
        tournament["id"],
    )
    upper_winners = [match["home_team_id"] for match in opening_matches]
    upper_losers = [match["away_team_id"] for match in opening_matches]

    for match, winner_team_id in zip(opening_matches, upper_winners):
        complete_match(client, owner["access_token"], match, winner_team_id)

    matches = list_tournament_matches(client, tournament["id"])
    upper_final = next(
        match
        for match in matches
        if match["stage"] == "Upper bracket" and match["round_number"] == 2
    )
    lower_round_one = next(
        match
        for match in matches
        if match["stage"] == "Lower bracket" and match["round_number"] == 1
    )

    assert {upper_final["home_team_id"], upper_final["away_team_id"]} == set(
        upper_winners
    )
    assert {lower_round_one["home_team_id"], lower_round_one["away_team_id"]} == set(
        upper_losers
    )

    lower_round_one_winner = lower_round_one["home_team_id"]
    complete_match(
        client,
        owner["access_token"],
        lower_round_one,
        lower_round_one_winner,
    )
    complete_match(
        client,
        owner["access_token"],
        upper_final,
        upper_final["home_team_id"],
    )

    matches = list_tournament_matches(client, tournament["id"])
    lower_round_two = next(
        match
        for match in matches
        if match["stage"] == "Lower bracket" and match["round_number"] == 2
    )
    assert lower_round_one_winner in {
        lower_round_two["home_team_id"],
        lower_round_two["away_team_id"],
    }

    complete_match(
        client,
        owner["access_token"],
        lower_round_two,
        lower_round_two["home_team_id"],
    )

    matches = list_tournament_matches(client, tournament["id"])
    grand_final_matches = [
        match
        for match in matches
        if match["stage"] == "Grand final" and match["round_number"] == 1
    ]

    assert len(grand_final_matches) == 1
    assert {
        grand_final_matches[0]["home_team_id"],
        grand_final_matches[0]["away_team_id"],
    } == {upper_final["home_team_id"], lower_round_two["home_team_id"]}


def test_swiss_generates_next_round_after_current_round_is_completed(client):
    owner = register_user(client, "owner_swiss", "owner-swiss@example.com")
    tournament = create_tournament(
        client,
        owner["access_token"],
        name="Swiss Auto Cup",
        status="REGISTRATION_OPEN",
        tournament_format="swiss",
    )
    create_registered_teams(
        client,
        owner["access_token"],
        tournament["id"],
        count=4,
    )
    close_registration(client, owner["access_token"], tournament["id"])

    round_one_matches = generate_bracket(
        client,
        owner["access_token"],
        tournament["id"],
    )

    for match in round_one_matches:
        complete_match(client, owner["access_token"], match, match["home_team_id"])

    matches = list_tournament_matches(client, tournament["id"])
    round_two_matches = [
        match
        for match in matches
        if match["stage"] == "Swiss" and match["round_number"] == 2
    ]

    assert len(round_two_matches) == 2
    assert {match["status"] for match in round_two_matches} == {"SCHEDULED"}

    played_pairs = {
        tuple(sorted((match["home_team_id"], match["away_team_id"])))
        for match in matches
    }
    assert len(played_pairs) == 4
