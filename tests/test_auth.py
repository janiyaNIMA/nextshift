from fastapi import status
from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "ok", "app": "NextShift"}


def test_student_registration_success(client: TestClient):
    payload = {
        "name": "Kamal Perera",
        "email": "kamal@student.campus.ac.lk",
        "password": "SecretPassword123!",
        "role": "student",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["email"] == "kamal@student.campus.ac.lk"
    assert data["role"] == "student"
    assert data["is_active"] is True
    assert data["is_approved"] is True  # Students are approved immediately


def test_employer_registration_starts_unapproved(client: TestClient):
    payload = {
        "name": "Campus Cafe Ltd",
        "email": "hiring@campuscafe.com",
        "password": "EmployerSecret123!",
        "role": "employer",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["email"] == "hiring@campuscafe.com"
    assert data["role"] == "employer"
    assert data["is_active"] is True
    assert data["is_approved"] is False  # Requires admin approval


def test_registration_duplicate_email_rejected(client: TestClient):
    payload = {
        "name": "Duplicate User",
        "email": "dup@example.com",
        "password": "Password123!",
        "role": "student",
    }
    res1 = client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == status.HTTP_201_CREATED

    res2 = client.post("/api/v1/auth/register", json=payload)
    assert res2.status_code == status.HTTP_409_CONFLICT
    assert "already exists" in res2.json()["detail"]


def test_login_success(client: TestClient):
    payload = {
        "name": "Login Tester",
        "email": "tester@example.com",
        "password": "MyStrongPassword123!",
        "role": "student",
    }
    client.post("/api/v1/auth/register", json=payload)

    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "tester@example.com", "password": "MyStrongPassword123!"},
    )
    assert login_resp.status_code == status.HTTP_200_OK
    token_data = login_resp.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"


def test_login_invalid_password(client: TestClient):
    payload = {
        "name": "Invalid Pass User",
        "email": "passcheck@example.com",
        "password": "CorrectPassword123!",
        "role": "student",
    }
    client.post("/api/v1/auth/register", json=payload)

    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "passcheck@example.com", "password": "WrongPassword!"},
    )
    assert login_resp.status_code == status.HTTP_401_UNAUTHORIZED


def test_auth_me_profile(client: TestClient, student_headers: dict[str, str]):
    response = client.get("/api/v1/auth/me", headers=student_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == "student@example.com"
    assert data["role"] == "student"


def test_auth_me_unauthenticated_fails(client: TestClient):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
