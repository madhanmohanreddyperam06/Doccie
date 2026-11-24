"""Unit and Integration Tests for PostgreSQL & JWT Authentication and TODO CRUD."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


@pytest.fixture(scope="module")
def registered_user():
    """Register a test user and return credentials."""
    user_data = {
        "email": "testuser@example.com",
        "username": "testuser",
        "password": "StrongPassword123!",
        "full_name": "Test User",
    }
    # Register user
    res = client.post("/auth/register", json=user_data)
    assert res.status_code in (201, 400)  # 400 if already exists in persistent test DB

    # Login to obtain JWT
    login_res = client.post(
        "/auth/login",
        json={"username_or_email": user_data["username"], "password": user_data["password"]},
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]

    return {
        **user_data,
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"},
    }


def test_register_new_user():
    """Test user registration with valid payload."""
    payload = {
        "email": "unique_new_user@example.com",
        "username": "uniquename",
        "password": "SecretPassword123!",
        "full_name": "Unique Developer",
    }
    response = client.post("/auth/register", json=payload)
    if response.status_code == 400 and "exists" in response.text:
        pass  # Previously created in local test DB
    else:
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == payload["email"]
        assert data["username"] == payload["username"]
        assert "hashed_password" not in data
        assert data["is_active"] is True


def test_register_duplicate_email_fails():
    """Test duplicate email rejection."""
    payload = {
        "email": "duplicate@example.com",
        "username": "userone",
        "password": "Password123!",
    }
    client.post("/auth/register", json=payload)

    # Attempt registration with same email
    dup_payload = {
        "email": "duplicate@example.com",
        "username": "usertwo",
        "password": "Password123!",
    }
    response = client.post("/auth/register", json=dup_payload)
    assert response.status_code == 400
    assert "email" in response.json()["detail"].lower()


def test_login_success_and_invalid_password():
    """Test successful login and password rejection."""
    user_data = {
        "email": "auth_check@example.com",
        "username": "authcheck",
        "password": "SecurePassword123!",
    }
    client.post("/auth/register", json=user_data)

    # Valid login with username
    res_ok = client.post(
        "/auth/login",
        json={"username_or_email": "authcheck", "password": "SecurePassword123!"},
    )
    assert res_ok.status_code == 200
    token_data = res_ok.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
    assert token_data["user"]["username"] == "authcheck"

    # Valid login with email
    res_email_ok = client.post(
        "/auth/login",
        json={"username_or_email": "auth_check@example.com", "password": "SecurePassword123!"},
    )
    assert res_email_ok.status_code == 200

    # Invalid password
    res_bad = client.post(
        "/auth/login",
        json={"username_or_email": "authcheck", "password": "WrongPassword!"},
    )
    assert res_bad.status_code == 401


def test_oauth2_form_login(registered_user):
    """Test OAuth2 password request form endpoint for Swagger UI."""
    response = client.post(
        "/auth/token",
        data={"username": registered_user["username"], "password": registered_user["password"]},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_get_current_user_profile(registered_user):
    """Test GET /auth/me returns authenticated user details."""
    response = client.get("/auth/me", headers=registered_user["headers"])
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == registered_user["username"]
    assert data["email"] == registered_user["email"]


def test_get_profile_unauthorized():
    """Test GET /auth/me without token returns 401."""
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_todos_crud_lifecycle(registered_user):
    """Test full CRUD lifecycle for TODO items with user authentication."""
    headers = registered_user["headers"]

    # 1. Create Todo
    create_res = client.post(
        "/todos",
        headers=headers,
        json={
            "title": "Configure PostgreSQL Migration",
            "description": "Set up Alembic migrations and verify PostgreSQL database tables.",
            "priority": "high",
        },
    )
    assert create_res.status_code == 201
    todo = create_res.json()
    todo_id = todo["id"]
    assert todo["title"] == "Configure PostgreSQL Migration"
    assert todo["priority"] == "high"
    assert todo["status"] == "pending"

    # 2. List Todos
    list_res = client.get("/todos", headers=headers)
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total"] >= 1
    assert any(t["id"] == todo_id for t in list_data["items"])

    # 3. Update Todo
    update_res = client.put(
        f"/todos/{todo_id}",
        headers=headers,
        json={"status": "completed"},
    )
    assert update_res.status_code == 200
    assert update_res.json()["status"] == "completed"

    # 4. Get Single Todo
    get_res = client.get(f"/todos/{todo_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["status"] == "completed"

    # 5. Delete Todo
    del_res = client.delete(f"/todos/{todo_id}", headers=headers)
    assert del_res.status_code == 200

    # Verify deletion
    verify_res = client.get(f"/todos/{todo_id}", headers=headers)
    assert verify_res.status_code == 404

