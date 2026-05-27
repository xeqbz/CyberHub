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


def test_list_team_members_returns_owner(client):
    owner = register_user(client, "vadim", "vadim@example.com")
    team = create_team(client, owner["access_token"])

    response = client.get(f"/api/v1/teams/{team['id']}/members")

    assert response.status_code == 200
    data = response.json()

    assert len(data) == 1
    assert data[0]["role"] == "OWNER"
    assert data[0]["user"]["username"] == "vadim"


def test_owner_can_add_member(client):
    owner = register_user(client, "vadim", "vadim@example.com")
    register_user(client, "alex", "alex@example.com")
    team = create_team(client, owner["access_token"])

    response = client.post(
        f"/api/v1/teams/{team['id']}/members",
        json={
            "user_id": 2,
            "role": "MEMBER",
        },
        headers=auth_headers(owner["access_token"]),
    )

    assert response.status_code == 201
    data = response.json()

    assert data["user_id"] == 2
    assert data["role"] == "MEMBER"
    assert data["user"]["username"] == "alex"


def test_owner_can_invite_member_by_username(client):
    owner = register_user(client, "vadim", "vadim@example.com")
    invited = register_user(client, "alex", "alex@example.com")
    team = create_team(client, owner["access_token"])

    response = client.post(
        f"/api/v1/teams/{team['id']}/invitations",
        json={
            "username": "alex",
            "role": "MEMBER",
        },
        headers=auth_headers(owner["access_token"]),
    )

    assert response.status_code == 201
    invitation = response.json()
    assert invitation["status"] == "PENDING"
    assert invitation["invited_user"]["username"] == "alex"

    members_response = client.get(f"/api/v1/teams/{team['id']}/members")
    assert len(members_response.json()) == 1

    notifications_response = client.get(
        "/api/v1/notifications",
        headers=auth_headers(invited["access_token"]),
    )
    assert notifications_response.status_code == 200
    assert notifications_response.json()[0]["title"] == "Team invitation"


def test_invited_user_can_accept_invitation(client):
    owner = register_user(client, "vadim", "vadim@example.com")
    invited = register_user(client, "alex", "alex@example.com")
    team = create_team(client, owner["access_token"])
    invitation = client.post(
        f"/api/v1/teams/{team['id']}/invitations",
        json={
            "username": "alex",
            "role": "MEMBER",
        },
        headers=auth_headers(owner["access_token"]),
    ).json()

    response = client.post(
        f"/api/v1/teams/invitations/{invitation['id']}/accept",
        headers=auth_headers(invited["access_token"]),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "ACCEPTED"

    members_response = client.get(f"/api/v1/teams/{team['id']}/members")
    members = members_response.json()
    assert len(members) == 2
    assert {item["user"]["username"] for item in members} == {"vadim", "alex"}


def test_only_invited_user_can_accept_invitation(client):
    owner = register_user(client, "vadim", "vadim@example.com")
    invited = register_user(client, "alex", "alex@example.com")
    other = register_user(client, "john", "john@example.com")
    team = create_team(client, owner["access_token"])
    invitation = client.post(
        f"/api/v1/teams/{team['id']}/invitations",
        json={
            "username": "alex",
            "role": "MEMBER",
        },
        headers=auth_headers(owner["access_token"]),
    ).json()

    response = client.post(
        f"/api/v1/teams/invitations/{invitation['id']}/accept",
        headers=auth_headers(other["access_token"]),
    )

    assert invited["access_token"]
    assert response.status_code == 403
    assert response.json()["detail"] == "Only invited user can perform this action"


def test_cannot_spam_team_invitations(client):
    owner = register_user(client, "vadim", "vadim@example.com")
    invited = register_user(client, "alex", "alex@example.com")
    team = create_team(client, owner["access_token"])

    first_response = client.post(
        f"/api/v1/teams/{team['id']}/invitations",
        json={
            "username": "alex",
            "role": "MEMBER",
        },
        headers=auth_headers(owner["access_token"]),
    )
    duplicate_response = client.post(
        f"/api/v1/teams/{team['id']}/invitations",
        json={
            "username": "alex",
            "role": "MEMBER",
        },
        headers=auth_headers(owner["access_token"]),
    )
    decline_response = client.post(
        f"/api/v1/teams/invitations/{first_response.json()['id']}/decline",
        headers=auth_headers(invited["access_token"]),
    )
    cooldown_response = client.post(
        f"/api/v1/teams/{team['id']}/invitations",
        json={
            "username": "alex",
            "role": "MEMBER",
        },
        headers=auth_headers(owner["access_token"]),
    )

    assert first_response.status_code == 201
    assert duplicate_response.status_code == 409
    assert duplicate_response.json()["detail"] == "User already has a pending invitation"
    assert decline_response.status_code == 200
    assert cooldown_response.status_code == 429
    assert cooldown_response.json()["detail"] == "Invitation was already sent recently"


def test_non_owner_cannot_add_member(client):
    owner = register_user(client, "vadim", "vadim@example.com")
    other_user = register_user(client, "alex", "alex@example.com")
    register_user(client, "john", "john@example.com")
    team = create_team(client, owner["access_token"])

    response = client.post(
        f"/api/v1/teams/{team['id']}/members",
        json={
            "user_id": 3,
            "role": "MEMBER",
        },
        headers=auth_headers(other_user["access_token"]),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Only team owner can perform this action"


def test_cannot_add_same_member_twice(client):
    owner = register_user(client, "vadim", "vadim@example.com")
    register_user(client, "alex", "alex@example.com")
    team = create_team(client, owner["access_token"])

    first_response = client.post(
        f"/api/v1/teams/{team['id']}/members",
        json={
            "user_id": 2,
            "role": "MEMBER",
        },
        headers=auth_headers(owner["access_token"]),
    )

    second_response = client.post(
        f"/api/v1/teams/{team['id']}/members",
        json={
            "user_id": 2,
            "role": "MEMBER",
        },
        headers=auth_headers(owner["access_token"]),
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json()["detail"] == "User is already a team member"


def test_owner_can_update_member_role(client):
    owner = register_user(client, "vadim", "vadim@example.com")
    register_user(client, "alex", "alex@example.com")
    team = create_team(client, owner["access_token"])

    client.post(
        f"/api/v1/teams/{team['id']}/members",
        json={
            "user_id": 2,
            "role": "MEMBER",
        },
        headers=auth_headers(owner["access_token"]),
    )

    response = client.patch(
        f"/api/v1/teams/{team['id']}/members/2",
        json={
            "role": "OWNER",
        },
        headers=auth_headers(owner["access_token"]),
    )

    assert response.status_code == 200
    data = response.json()

    assert data["user_id"] == 2
    assert data["role"] == "OWNER"


def test_cannot_change_original_owner_role(client):
    owner = register_user(client, "vadim", "vadim@example.com")
    team = create_team(client, owner["access_token"])

    response = client.patch(
        f"/api/v1/teams/{team['id']}/members/1",
        json={
            "role": "MEMBER",
        },
        headers=auth_headers(owner["access_token"]),
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Team owner role cannot be changed"


def test_owner_can_remove_member(client):
    owner = register_user(client, "vadim", "vadim@example.com")
    register_user(client, "alex", "alex@example.com")
    team = create_team(client, owner["access_token"])

    client.post(
        f"/api/v1/teams/{team['id']}/members",
        json={
            "user_id": 2,
            "role": "MEMBER",
        },
        headers=auth_headers(owner["access_token"]),
    )

    delete_response = client.delete(
        f"/api/v1/teams/{team['id']}/members/2",
        headers=auth_headers(owner["access_token"]),
    )

    assert delete_response.status_code == 204

    members_response = client.get(f"/api/v1/teams/{team['id']}/members")
    assert members_response.status_code == 200
    members = members_response.json()

    assert len(members) == 1
    assert members[0]["user_id"] == 1


def test_cannot_remove_team_owner(client):
    owner = register_user(client, "vadim", "vadim@example.com")
    team = create_team(client, owner["access_token"])

    response = client.delete(
        f"/api/v1/teams/{team['id']}/members/1",
        headers=auth_headers(owner["access_token"]),
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Team owner cannot be removed"
