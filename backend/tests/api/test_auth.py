def test_register_returns_token_pair(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword",
        },
    )

    assert response.status_code == 201
    data = response.json()

    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_register_duplicate_email_returns_409(client):
    payload = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword",
    }

    first_response = client.post("/api/v1/auth/register", json=payload)
    second_response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "another_user",
            "email": "test@example.com",
            "password": "anotherpassword",
        },
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json()["detail"] == "User with this email already exists"


def test_login_returns_token_pair_for_valid_credentials(client):
    register_payload = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword",
    }

    client.post("/api/v1/auth/register", json=register_payload)

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "testpassword"},
    )

    assert response.status_code == 200
    data = response.json()

    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_with_invalid_credentials_returns_401(client):
    register_payload = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword",
    }

    client.post("/api/v1/auth/register", json=register_payload)

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "wrongpassword"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_refresh_returns_new_token_pair(client):
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword",
        },
    )

    assert register_response.status_code == 201

    refresh_token = register_response.json()["refresh_token"]

    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )

    assert response.status_code == 200

    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_refresh_with_invalid_token_returns_401(client):
    response = client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": "invalid-token",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired refresh token"
