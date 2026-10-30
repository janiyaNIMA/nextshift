from datetime import UTC, datetime, timedelta

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_password_hash
from app.models.booking import Booking, BookingStatus
from app.models.job import Job, JobStatus
from app.models.user import User, UserRole


def _create_student(db_session: Session, idx: int) -> dict[str, str]:
    student = User(
        name=f"Student {idx}",
        email=f"student_algo_{idx}@example.com",
        password_hash=get_password_hash("Pass123!"),
        role=UserRole.STUDENT,
        is_active=True,
        is_approved=True,
    )
    db_session.add(student)
    db_session.commit()
    db_session.refresh(student)
    token = create_access_token(student.id, extra_claims={"role": "student", "email": student.email})
    return {"Authorization": f"Bearer {token}"}


def _create_employer(
    db_session: Session,
    idx: int,
    *,
    is_active: bool = True,
    is_approved: bool = True,
) -> User:
    employer = User(
        name=f"Employer {idx}",
        email=f"employer_algo_{idx}@example.com",
        password_hash=get_password_hash("Pass123!"),
        role=UserRole.EMPLOYER,
        is_active=is_active,
        is_approved=is_approved,
    )
    db_session.add(employer)
    db_session.commit()
    db_session.refresh(employer)
    return employer


def _create_job(
    db_session: Session,
    employer_id: int,
    *,
    title: str,
    status: JobStatus = JobStatus.PUBLISHED,
    starts_delta_days: int = 3,
    duration_hours: int = 4,
    capacity: int = 2,
    category: str = "Technology",
    location: str = "Main Campus",
) -> Job:
    now = datetime.now(UTC)
    starts_at = now + timedelta(days=starts_delta_days)
    job = Job(
        employer_id=employer_id,
        title=title,
        description=f"{title} description long enough",
        category=category,
        location=location,
        pay_amount=20.0,
        pay_unit="per_hour",
        starts_at=starts_at,
        ends_at=starts_at + timedelta(hours=duration_hours),
        capacity=capacity,
        status=status,
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    return job


def _book_job(db_session: Session, *, job_id: int, student_id: int) -> Booking:
    booking = Booking(
        job_id=job_id,
        student_id=student_id,
        status=BookingStatus.CONFIRMED,
    )
    db_session.add(booking)
    db_session.commit()
    db_session.refresh(booking)
    return booking


def test_same_unfiltered_feed_for_all_students(client: TestClient, db_session: Session):
    employer = _create_employer(db_session, 1, is_approved=True)
    _create_job(db_session, employer.id, title="Eligible Job A")
    _create_job(db_session, employer.id, title="Eligible Job B")

    headers1 = _create_student(db_session, 1)
    headers2 = _create_student(db_session, 2)

    res1 = client.get("/api/v1/jobs", headers=headers1)
    res2 = client.get("/api/v1/jobs", headers=headers2)

    assert res1.status_code == status.HTTP_200_OK
    assert res2.status_code == status.HTTP_200_OK
    assert [j["id"] for j in res1.json()] == [j["id"] for j in res2.json()]


def test_ineligible_jobs_are_hidden_from_discovery_feed(client: TestClient, db_session: Session):
    approved_employer = _create_employer(db_session, 2, is_approved=True)
    unapproved_employer = _create_employer(db_session, 3, is_approved=False)

    visible = _create_job(db_session, approved_employer.id, title="Visible Published Job")
    _create_job(db_session, approved_employer.id, title="Pending Job", status=JobStatus.PENDING)
    _create_job(db_session, approved_employer.id, title="Rejected Job", status=JobStatus.REJECTED)
    _create_job(db_session, approved_employer.id, title="Closed Job", status=JobStatus.CLOSED)
    _create_job(db_session, unapproved_employer.id, title="Unapproved Employer Job")
    _create_job(
        db_session,
        approved_employer.id,
        title="Started Job",
        starts_delta_days=-1,
        duration_hours=1,
    )
    _create_job(
        db_session,
        approved_employer.id,
        title="Expired Job",
        starts_delta_days=-3,
        duration_hours=1,
    )

    # Full capacity job should be hidden from discovery feed
    full_job = _create_job(db_session, approved_employer.id, title="Full Capacity Job", capacity=1)
    student_for_full = User(
        name="Booked Student",
        email="booked_student_algo@example.com",
        password_hash=get_password_hash("Pass123!"),
        role=UserRole.STUDENT,
        is_active=True,
        is_approved=True,
    )
    db_session.add(student_for_full)
    db_session.commit()
    db_session.refresh(student_for_full)
    _book_job(db_session, job_id=full_job.id, student_id=student_for_full.id)

    headers = _create_student(db_session, 4)
    res = client.get("/api/v1/jobs", headers=headers)
    assert res.status_code == status.HTTP_200_OK

    ids = [j["id"] for j in res.json()]
    assert visible.id in ids
    assert full_job.id not in ids


def test_recommendation_ordering_is_newest_first(client: TestClient, db_session: Session):
    employer = _create_employer(db_session, 4, is_approved=True)
    older = _create_job(db_session, employer.id, title="Older Job")
    newer = _create_job(db_session, employer.id, title="Newer Job")

    headers = _create_student(db_session, 5)
    res = client.get("/api/v1/jobs", headers=headers)
    assert res.status_code == status.HTTP_200_OK
    ids = [j["id"] for j in res.json()]

    # Latest inserts should appear first due to created_at desc, id desc.
    assert ids.index(newer.id) < ids.index(older.id)


def test_pagination_and_optional_filters(client: TestClient, db_session: Session):
    employer = _create_employer(db_session, 5, is_approved=True)

    _create_job(db_session, employer.id, title="Tech Colombo", category="Tech", location="Colombo")
    _create_job(db_session, employer.id, title="Tech Kandy", category="Tech", location="Kandy")
    _create_job(db_session, employer.id, title="Design Colombo", category="Design", location="Colombo")

    headers = _create_student(db_session, 6)

    filtered = client.get("/api/v1/jobs?category=Tech&location=Kandy", headers=headers)
    assert filtered.status_code == status.HTTP_200_OK
    filtered_data = filtered.json()
    assert len(filtered_data) == 1
    assert filtered_data[0]["title"] == "Tech Kandy"

    page1 = client.get("/api/v1/jobs?skip=0&limit=2", headers=headers)
    page2 = client.get("/api/v1/jobs?skip=2&limit=2", headers=headers)
    assert page1.status_code == status.HTTP_200_OK
    assert page2.status_code == status.HTTP_200_OK

    ids1 = [j["id"] for j in page1.json()]
    ids2 = [j["id"] for j in page2.json()]
    assert len(ids1) <= 2
    assert len(ids2) <= 2
    assert not set(ids1).intersection(set(ids2))


def test_empty_feed_when_no_eligible_jobs(client: TestClient):
    res = client.get("/api/v1/jobs")
    assert res.status_code == status.HTTP_200_OK
    assert res.json() == []


def test_no_auth_regression_for_public_discovery_feed(client: TestClient, db_session: Session):
    employer = _create_employer(db_session, 6, is_approved=True)
    _create_job(db_session, employer.id, title="Public Feed Job")

    # Endpoint must remain public.
    res = client.get("/api/v1/jobs")
    assert res.status_code == status.HTTP_200_OK
    assert len(res.json()) >= 1
