from tests.api.helpers import (
    auth_headers,
    bootstrap_admin,
    complete_match,
    prepare_match_context,
    register_user,
)


def _complete_context_match(client, context: dict) -> None:
    complete_match(
        client,
        context["owner"]["access_token"],
        context["match"]["id"],
        context["home_team"]["id"],
    )


def _create_dispute(client, access_token: str, match_id: int) -> dict:
    response = client.post(
        "/api/v1/disputes",
        json={
            "match_id": match_id,
            "reason": "The reported score needs moderator review.",
        },
        headers=auth_headers(access_token),
    )
    assert response.status_code == 201
    return response.json()


def _resolve_dispute(
    client,
    admin_access_token: str,
    dispute_id: int,
    status: str = "RESOLVED",
) -> dict:
    response = client.patch(
        f"/api/v1/admin/disputes/{dispute_id}/resolve",
        json={
            "status": status,
            "resolution": "Reviewed evidence and confirmed the final decision.",
        },
        headers=auth_headers(admin_access_token),
    )
    assert response.status_code == 200
    return response.json()


def test_user_can_create_match_dispute(client):
    context = prepare_match_context(client)
    _complete_context_match(client, context)

    dispute = _create_dispute(
        client,
        context["away_owner"]["access_token"],
        context["match"]["id"],
    )

    assert dispute["match_id"] == context["match"]["id"]
    assert dispute["status"] == "OPEN"
    assert dispute["opened_by"]["username"] == "away_owner"


def test_admin_can_change_dispute_status(client):
    context = prepare_match_context(client)
    _complete_context_match(client, context)
    dispute = _create_dispute(
        client,
        context["away_owner"]["access_token"],
        context["match"]["id"],
    )
    admin = register_user(client, "admin", "admin@example.com")
    bootstrap_admin(client, admin)

    resolved = _resolve_dispute(client, admin["access_token"], dispute["id"])

    assert resolved["status"] == "RESOLVED"
    assert resolved["resolved_by"]["username"] == "admin"


def test_dispute_resolution_is_saved(client):
    context = prepare_match_context(client)
    _complete_context_match(client, context)
    dispute = _create_dispute(
        client,
        context["away_owner"]["access_token"],
        context["match"]["id"],
    )
    admin = register_user(client, "admin", "admin@example.com")
    bootstrap_admin(client, admin)

    resolved = _resolve_dispute(client, admin["access_token"], dispute["id"])

    assert resolved["resolution"] == (
        "Reviewed evidence and confirmed the final decision."
    )
    assert resolved["resolved_at"] is not None


def test_cannot_reopen_closed_dispute(client):
    context = prepare_match_context(client)
    _complete_context_match(client, context)
    dispute = _create_dispute(
        client,
        context["away_owner"]["access_token"],
        context["match"]["id"],
    )
    admin = register_user(client, "admin", "admin@example.com")
    bootstrap_admin(client, admin)
    _resolve_dispute(client, admin["access_token"], dispute["id"])

    response = client.post(
        "/api/v1/disputes",
        json={
            "match_id": context["match"]["id"],
            "reason": "Trying to open the same dispute again.",
        },
        headers=auth_headers(context["away_owner"]["access_token"]),
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "You already created a dispute for this match"


def test_dispute_resolution_notifies_opening_user(client):
    context = prepare_match_context(client)
    _complete_context_match(client, context)
    dispute = _create_dispute(
        client,
        context["away_owner"]["access_token"],
        context["match"]["id"],
    )
    admin = register_user(client, "admin", "admin@example.com")
    bootstrap_admin(client, admin)

    _resolve_dispute(client, admin["access_token"], dispute["id"])

    response = client.get(
        "/api/v1/notifications",
        headers=auth_headers(context["away_owner"]["access_token"]),
    )
    assert response.status_code == 200
    assert any(item["title"] == "Dispute reviewed" for item in response.json())
