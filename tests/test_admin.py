from datetime import UTC, datetime, timedelta

from fastapi import status
from fastapi.testclient import TestClient

from app.models.user import User


def test_admin_approves_employer(
    client: TestClient,
    admin_headers: dict[str, str],
    unapproved_employer: User,
):
    # Check pending list
    res = client.get("/api/v1/admin/employers/pending", headers=admin_headers)
    assert res.status_code == status.HTTP_200_OK
    pending_ids = [u["id"] for u in res.json()]
    assert unapproved_employer.id in pending_ids

    # Approve
    approve_res = client.patch(
        f"/api/v1/admin/employers/{unapproved_employer.id}/approve",
        headers=admin_headers,
    )
    assert approve_res.status_code == status.HTTP_200_OK
    assert approve_res.json()["is_approved"] is True


def test_admin_approves_job_and_appears_publicly(
    client: TestClient,
    admin_headers: dict[str, str],
    employer_headers: dict[str, str],
):
    now = datetime.now(UTC)
    create_res = client.post(
        "/api/v1/jobs",
        json={
            "title": "IT Lab Assistant",
            "description": "Help students with lab computer troubleshooting",
            "category": "Technology",
            "location": "Computer Center",
            "pay_amount": 18.0,
            "pay_unit": "per_hour",
            "starts_at": (now + timedelta(days=5)).isoformat(),
            "ends_at": (now + timedelta(days=5, hours=4)).isoformat(),
            "capacity": 3,
        },
        headers=employer_headers,
    )
    job_id = create_res.json()["id"]

    # Pending in admin list
    pending_jobs_res = client.get("/api/v1/admin/jobs/pending", headers=admin_headers)
    assert pending_jobs_res.status_code == status.HTTP_200_OK
    assert any(j["id"] == job_id for j in pending_jobs_res.json())

    # Approve job
    approve_res = client.patch(f"/api/v1/admin/jobs/{job_id}/approve", headers=admin_headers)
    assert approve_res.status_code == status.HTTP_200_OK
    assert approve_res.json()["status"] == "published"

    # Job is now visible in public list
    public_res = client.get("/api/v1/jobs")
    assert any(j["id"] == job_id for j in public_res.json())

    # Job detail view works
    public_detail = client.get(f"/api/v1/jobs/{job_id}")
    assert public_detail.status_code == status.HTTP_200_OK
    assert public_detail.json()["remaining_capacity"] == 3


def test_non_admin_cannot_access_admin_endpoints(
    client: TestClient,
    student_headers: dict[str, str],
    employer_headers: dict[str, str],
):
    assert (
        client.get("/api/v1/admin/employers/pending", headers=student_headers).status_code == status.HTTP_403_FORBIDDEN
    )
    assert client.get("/api/v1/admin/jobs/pending", headers=employer_headers).status_code == status.HTTP_403_FORBIDDEN
