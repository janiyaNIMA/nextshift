from datetime import UTC, datetime, timedelta

from fastapi import status
from fastapi.testclient import TestClient


def test_approved_employer_creates_job_starts_pending(
    client: TestClient,
    employer_headers: dict[str, str],
):
    now = datetime.now(UTC)
    payload = {
        "title": "Lab Assistant",
        "description": "Prepare biology lab equipment and maintain inventory",
        "category": "Academic",
        "location": "Science Block 3",
        "pay_amount": 20.0,
        "pay_unit": "per_hour",
        "starts_at": (now + timedelta(days=3)).isoformat(),
        "ends_at": (now + timedelta(days=3, hours=5)).isoformat(),
        "capacity": 2,
    }
    response = client.post("/api/v1/jobs", json=payload, headers=employer_headers)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["title"] == "Lab Assistant"
    assert data["status"] == "pending"  # Crucial rule: new jobs always start as pending


def test_unapproved_employer_cannot_create_job(
    client: TestClient,
    unapproved_employer_headers: dict[str, str],
):
    now = datetime.now(UTC)
    payload = {
        "title": "Unapproved Job",
        "description": "Should not be allowed to post",
        "category": "Retail",
        "location": "Campus Center",
        "pay_amount": 10.0,
        "pay_unit": "per_hour",
        "starts_at": (now + timedelta(days=1)).isoformat(),
        "ends_at": (now + timedelta(days=1, hours=2)).isoformat(),
        "capacity": 1,
    }
    response = client.post("/api/v1/jobs", json=payload, headers=unapproved_employer_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_student_cannot_create_job(
    client: TestClient,
    student_headers: dict[str, str],
):
    now = datetime.now(UTC)
    payload = {
        "title": "Student Created Job",
        "description": "Should fail with forbidden",
        "category": "Other",
        "location": "Hostel",
        "pay_amount": 10.0,
        "pay_unit": "per_hour",
        "starts_at": (now + timedelta(days=1)).isoformat(),
        "ends_at": (now + timedelta(days=1, hours=2)).isoformat(),
        "capacity": 1,
    }
    response = client.post("/api/v1/jobs", json=payload, headers=student_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_invalid_dates_and_capacity_rejected(
    client: TestClient,
    employer_headers: dict[str, str],
):
    now = datetime.now(UTC)
    # ends_at earlier than starts_at
    payload_bad_dates = {
        "title": "Invalid Dates",
        "description": "Valid description length test",
        "category": "Other",
        "location": "Library",
        "pay_amount": 10.0,
        "pay_unit": "per_hour",
        "starts_at": (now + timedelta(days=2)).isoformat(),
        "ends_at": (now + timedelta(days=1)).isoformat(),
        "capacity": 1,
    }
    res1 = client.post("/api/v1/jobs", json=payload_bad_dates, headers=employer_headers)
    assert res1.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    # capacity < 1
    payload_bad_capacity = {
        "title": "Invalid Capacity",
        "description": "Valid description length test",
        "category": "Other",
        "location": "Library",
        "pay_amount": 10.0,
        "pay_unit": "per_hour",
        "starts_at": (now + timedelta(days=1)).isoformat(),
        "ends_at": (now + timedelta(days=1, hours=2)).isoformat(),
        "capacity": 0,
    }
    res2 = client.post("/api/v1/jobs", json=payload_bad_capacity, headers=employer_headers)
    assert res2.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    # negative pay
    payload_bad_pay = {
        "title": "Invalid Pay",
        "description": "Valid description length test",
        "category": "Other",
        "location": "Library",
        "pay_amount": -5.0,
        "pay_unit": "per_hour",
        "starts_at": (now + timedelta(days=1)).isoformat(),
        "ends_at": (now + timedelta(days=1, hours=2)).isoformat(),
        "capacity": 1,
    }
    res3 = client.post("/api/v1/jobs", json=payload_bad_pay, headers=employer_headers)
    assert res3.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_pending_job_invisible_in_public_list(
    client: TestClient,
    employer_headers: dict[str, str],
):
    now = datetime.now(UTC)
    create_res = client.post(
        "/api/v1/jobs",
        json={
            "title": "Secret Job",
            "description": "This job should be pending and invisible",
            "category": "Admin",
            "location": "Admin Office",
            "pay_amount": 12.0,
            "pay_unit": "per_hour",
            "starts_at": (now + timedelta(days=1)).isoformat(),
            "ends_at": (now + timedelta(days=1, hours=3)).isoformat(),
            "capacity": 1,
        },
        headers=employer_headers,
    )
    job_id = create_res.json()["id"]

    # Public list should NOT include this pending job
    list_res = client.get("/api/v1/jobs")
    assert list_res.status_code == status.HTTP_200_OK
    job_ids = [j["id"] for j in list_res.json()]
    assert job_id not in job_ids

    # Public detail should return 404
    detail_res = client.get(f"/api/v1/jobs/{job_id}")
    assert detail_res.status_code == status.HTTP_404_NOT_FOUND


def test_employer_can_view_own_jobs(
    client: TestClient,
    employer_headers: dict[str, str],
):
    resp = client.get("/api/v1/employer/jobs", headers=employer_headers)
    assert resp.status_code == status.HTTP_200_OK
    assert isinstance(resp.json(), list)
