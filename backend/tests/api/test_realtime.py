from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from app.main import app
from app.modules.platform.model import (
    ActionLog,
    MatchmakingRequest,
    MatchmakingRequestStatus,
    Notification,
)
from app.modules.platform.service import (
    create_notification,
    expire_stale_matchmaking_requests,
)
from tests.api.helpers import auth_headers, register_user


def test_notifications_websocket_sends_current_snapshot(
    client,
    test_session_factory,
):
    user = register_user(client, "alpha", "alpha@example.com")
    profile = client.get(
        "/api/v1/users/me",
        headers=auth_headers(user["access_token"]),
    ).json()

    db = test_session_factory()
    try:
        create_notification(
            db,
            user_id=profile["id"],
            title="Live update",
            message="Realtime notification payload",
        )
    finally:
        db.close()

    with TestClient(app) as live_client:
        with live_client.websocket_connect(
            f"/ws/notifications?token={user['access_token']}"
        ) as websocket:
            event = websocket.receive_json()

    assert event["type"] == "notifications.snapshot"
    assert event["payload"]["total_count"] == 1
    assert event["payload"]["unread_count"] == 1
    assert event["payload"]["notifications"][0]["title"] == "Live update"


def test_expire_stale_matchmaking_requests_creates_notification_and_log(
    client,
    test_session_factory,
):
    user = register_user(client, "alpha", "alpha@example.com")
    profile = client.get(
        "/api/v1/users/me",
        headers=auth_headers(user["access_token"]),
    ).json()

    db = test_session_factory()
    try:
        request = MatchmakingRequest(
            user_id=profile["id"],
            rating_snapshot=1000,
            created_at=datetime.now(UTC) - timedelta(minutes=45),
            updated_at=datetime.now(UTC) - timedelta(minutes=45),
        )
        db.add(request)
        db.commit()
        db.refresh(request)

        expired = expire_stale_matchmaking_requests(
            db,
            max_age_minutes=30,
            now=datetime.now(UTC),
        )

        db.refresh(request)
        notification = db.query(Notification).filter_by(user_id=profile["id"]).one()
        action_log = db.query(ActionLog).filter_by(
            action="ranked_matchmaking_expired"
        ).one()
    finally:
        db.close()

    assert expired == 1
    assert request.status == MatchmakingRequestStatus.CANCELLED
    assert notification.title == "Matchmaking expired"
    assert action_log.entity_id == request.id
