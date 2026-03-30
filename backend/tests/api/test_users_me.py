def test_users_me_requires_auth(client):
    response = client.get("/users/me")

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication credentials were not provided"


def test_users_me_returns_current_user(client):
    register_response = client.post(
        "/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword",
        },
    )

    token = register_response.json()["access_token"]

    response = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert data["is_active"] is True
    assert data["role"] == "USER"