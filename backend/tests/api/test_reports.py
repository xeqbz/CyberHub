import csv
from io import StringIO

from tests.api.helpers import (
    auth_headers,
    bootstrap_admin,
    create_ranked_match,
    register_user,
    submit_ranked_result,
)


def _read_csv_rows(text: str) -> list[dict[str, str]]:
    return list(csv.DictReader(StringIO(text)))


def test_report_export_requires_admin_or_organizer(client):
    user = register_user(client, "regular", "regular@example.com")

    response = client.get(
        "/api/v1/admin/reports/export?report_type=users",
        headers=auth_headers(user["access_token"]),
    )

    assert response.status_code == 403


def test_users_report_exports_readable_roles(client):
    admin = register_user(client, "admin", "admin@example.com")
    bootstrap_admin(client, admin)

    response = client.get(
        "/api/v1/admin/reports/export?report_type=users",
        headers=auth_headers(admin["access_token"]),
    )

    assert response.status_code == 200
    rows = _read_csv_rows(response.text)
    assert rows[0]["username"] == "admin"
    assert rows[0]["role"] == "ADMIN"


def test_player_statistics_report_exports_ranked_kda(client):
    admin = register_user(client, "admin", "admin@example.com")
    first = register_user(client, "alpha", "alpha@example.com")
    second = register_user(client, "bravo", "bravo@example.com")
    bootstrap_admin(client, admin)
    match = create_ranked_match(client, first, second)
    submit_ranked_result(
        client,
        first["access_token"],
        match["id"],
        player_one_score=2,
        player_two_score=0,
        player_one_kills=20,
        player_one_deaths=5,
        player_one_assists=10,
        player_two_kills=4,
        player_two_deaths=18,
        player_two_assists=2,
    )

    response = client.get(
        "/api/v1/admin/reports/export?report_type=player_statistics",
        headers=auth_headers(admin["access_token"]),
    )

    assert response.status_code == 200
    rows = {row["username"]: row for row in _read_csv_rows(response.text)}
    assert rows["alpha"]["ranked_matches"] == "1"
    assert rows["alpha"]["kills"] == "20"
    assert rows["alpha"]["kda"] == "6.0"
    assert rows["bravo"]["kda"] == "0.33"


def test_action_logs_report_exports_audit_entries(client):
    admin = register_user(client, "admin", "admin@example.com")
    bootstrap_admin(client, admin)

    response = client.get(
        "/api/v1/admin/reports/export?report_type=action_logs",
        headers=auth_headers(admin["access_token"]),
    )

    assert response.status_code == 200
    rows = _read_csv_rows(response.text)
    actions = {row["action"] for row in rows}
    assert "admin_bootstrapped" in actions
