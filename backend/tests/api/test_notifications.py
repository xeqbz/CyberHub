from tests.api.helpers import (
    auth_headers,
    complete_match,
    prepare_match_context,
)


def _list_notifications(client, access_token: str) -> list[dict]:
    response = client.get(
        "/api/v1/notifications",
        headers=auth_headers(access_token),
    )
    assert response.status_code == 200
    return response.json()


def test_match_creation_creates_notification(client):
    context = prepare_match_context(client)

    notifications = _list_notifications(client, context["owner"]["access_token"])

    assert any(item["title"] == "Match scheduled" for item in notifications)


def test_tournament_status_update_creates_notification(client):
    context = prepare_match_context(client)

    response = client.patch(
        f"/api/v1/tournaments/{context['tournament']['id']}",
        json={"status": "IN_PROGRESS"},
        headers=auth_headers(context["owner"]["access_token"]),
    )

    assert response.status_code == 200
    notifications = _list_notifications(client, context["owner"]["access_token"])
    assert any(item["title"] == "Tournament status updated" for item in notifications)


def test_match_result_update_creates_notification(client):
    context = prepare_match_context(client)

    complete_match(
        client,
        context["owner"]["access_token"],
        context["match"]["id"],
        context["home_team"]["id"],
    )

    notifications = _list_notifications(client, context["owner"]["access_token"])
    assert any(item["title"] == "Match result updated" for item in notifications)


def test_match_creation_does_not_duplicate_notifications_for_same_owner(client):
    context = prepare_match_context(client, same_owner=True)

    notifications = _list_notifications(client, context["owner"]["access_token"])
    scheduled = [
        item
        for item in notifications
        if item["title"] == "Match scheduled"
        and item["related_entity_id"] == context["match"]["id"]
    ]

    assert len(scheduled) == 1
