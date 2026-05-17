from tests.api.helpers import (
    auth_headers,
    bootstrap_admin,
    complete_match,
    create_team,
    create_tournament,
    prepare_match_context,
    register_user,
)


def _list_action_logs(
    client, access_token: str, action: str | None = None
) -> list[dict]:
    url = "/api/v1/admin/action-logs"
    if action is not None:
        url = f"{url}?action={action}"
    response = client.get(url, headers=auth_headers(access_token))
    assert response.status_code == 200
    return response.json()


def test_user_registration_is_written_to_audit_log(client):
    user = register_user(client, "audited", "audited@example.com")
    bootstrap_admin(client, user)

    logs = _list_action_logs(client, user["access_token"], "user_registered")

    assert len(logs) == 1
    assert logs[0]["entity_type"] == "user"
    assert logs[0]["details"]["username"] == "audited"


def test_team_member_changes_are_written_to_audit_log(client):
    owner = register_user(client, "owner", "owner@example.com")
    member = register_user(client, "member", "member@example.com")
    bootstrap_admin(client, owner)
    team = create_team(client, owner["access_token"], "Audit Team")

    add_response = client.post(
        f"/api/v1/teams/{team['id']}/members",
        json={"user_id": 2, "role": "MEMBER"},
        headers=auth_headers(owner["access_token"]),
    )
    assert add_response.status_code == 201

    remove_response = client.delete(
        f"/api/v1/teams/{team['id']}/members/2",
        headers=auth_headers(owner["access_token"]),
    )
    assert remove_response.status_code == 204

    logs = _list_action_logs(client, owner["access_token"])
    actions = {item["action"] for item in logs}
    assert member["access_token"]
    assert "team_member_added" in actions
    assert "team_member_removed" in actions


def test_tournament_update_is_written_to_audit_log(client):
    owner = register_user(client, "owner", "owner@example.com")
    bootstrap_admin(client, owner)
    tournament = create_tournament(client, owner["access_token"], "Audit Cup")

    response = client.patch(
        f"/api/v1/tournaments/{tournament['id']}",
        json={"status": "REGISTRATION_CLOSED"},
        headers=auth_headers(owner["access_token"]),
    )
    assert response.status_code == 200

    logs = _list_action_logs(client, owner["access_token"], "tournament_updated")

    assert len(logs) == 1
    assert logs[0]["entity_id"] == tournament["id"]
    assert logs[0]["details"]["status"] == "REGISTRATION_CLOSED"


def test_dispute_resolution_is_written_to_audit_log(client):
    context = prepare_match_context(client)
    complete_match(
        client,
        context["owner"]["access_token"],
        context["match"]["id"],
        context["home_team"]["id"],
    )
    dispute_response = client.post(
        "/api/v1/disputes",
        json={
            "match_id": context["match"]["id"],
            "reason": "The result needs an audit trail.",
        },
        headers=auth_headers(context["away_owner"]["access_token"]),
    )
    assert dispute_response.status_code == 201
    admin = register_user(client, "admin", "admin@example.com")
    bootstrap_admin(client, admin)

    resolve_response = client.patch(
        f"/api/v1/admin/disputes/{dispute_response.json()['id']}/resolve",
        json={
            "status": "RESOLVED",
            "resolution": "Resolution was saved to the audit log.",
        },
        headers=auth_headers(admin["access_token"]),
    )
    assert resolve_response.status_code == 200

    logs = _list_action_logs(client, admin["access_token"], "admin_dispute_resolved")

    assert len(logs) == 1
    assert logs[0]["entity_id"] == dispute_response.json()["id"]
    assert logs[0]["details"]["status"] == "RESOLVED"
