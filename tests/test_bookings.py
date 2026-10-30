import concurrent.futures
from datetime import UTC, datetime, timedelta

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.security import create_access_token, get_password_hash
from app.main import app
from app.models.job import Job, JobStatus
from app.models.user import User, UserRole
from tests.conftest import TestingSessionLocal


def test_student_can_book_published_job(
    client: TestClient,
    student_headers: dict[str, str],
    published_job: Job,
):
    response = client.post(
        f"/api/v1/jobs/{published_job.id}/bookings",
        headers=student_headers,
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["job_id"] == published_job.id
    assert data["status"] == "confirmed"


def test_employer_cannot_book_job(
    client: TestClient,
    employer_headers: dict[str, str],
    published_job: Job,
):
    response = client.post(
        f"/api/v1/jobs/{published_job.id}/bookings",
        headers=employer_headers,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_duplicate_booking_rejected(
    client: TestClient,
    student_headers: dict[str, str],
    published_job: Job,
):
    res1 = client.post(
        f"/api/v1/jobs/{published_job.id}/bookings",
        headers=student_headers,
    )
    assert res1.status_code == status.HTTP_201_CREATED

    res2 = client.post(
        f"/api/v1/jobs/{published_job.id}/bookings",
        headers=student_headers,
    )
    assert res2.status_code == status.HTTP_409_CONFLICT
    assert "already booked" in res2.json()["detail"]


def test_full_capacity_booking_rejected(
    client: TestClient,
    db_session: Session,
    approved_employer: User,
):
    # Create job with capacity = 1
    now = datetime.now(UTC)
    job = Job(
        employer_id=approved_employer.id,
        title="Single Slot Job",
        description="Only one person can book this vacancy",
        category="Events",
        location="Auditorium",
        pay_amount=25.0,
        pay_unit="per_event",
        starts_at=now + timedelta(days=2),
        ends_at=now + timedelta(days=2, hours=3),
        capacity=1,
        status=JobStatus.PUBLISHED,
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    # First student books
    student1 = User(
        name="Student One",
        email="student1@example.com",
        password_hash=get_password_hash("Pass123!"),
        role=UserRole.STUDENT,
        is_active=True,
        is_approved=True,
    )
    db_session.add(student1)
    db_session.commit()
    db_session.refresh(student1)
    token1 = create_access_token(student1.id, extra_claims={"role": "student", "email": student1.email})
    headers1 = {"Authorization": f"Bearer {token1}"}

    res1 = client.post(f"/api/v1/jobs/{job.id}/bookings", headers=headers1)
    assert res1.status_code == status.HTTP_201_CREATED

    # Second student tries to book -> should fail with 409
    student2 = User(
        name="Student Two",
        email="student2@example.com",
        password_hash=get_password_hash("Pass123!"),
        role=UserRole.STUDENT,
        is_active=True,
        is_approved=True,
    )
    db_session.add(student2)
    db_session.commit()
    db_session.refresh(student2)
    token2 = create_access_token(student2.id, extra_claims={"role": "student", "email": student2.email})
    headers2 = {"Authorization": f"Bearer {token2}"}

    res2 = client.post(f"/api/v1/jobs/{job.id}/bookings", headers=headers2)
    assert res2.status_code == status.HTTP_409_CONFLICT
    assert "maximum booking capacity" in res2.json()["detail"]


def test_cannot_book_past_job(
    client: TestClient,
    student_headers: dict[str, str],
    db_session: Session,
    approved_employer: User,
):
    past_time = datetime.now(UTC) - timedelta(days=1)
    past_job = Job(
        employer_id=approved_employer.id,
        title="Past Event",
        description="This event already happened in the past",
        category="Events",
        location="Campus Field",
        pay_amount=15.0,
        pay_unit="per_hour",
        starts_at=past_time,
        ends_at=past_time + timedelta(hours=2),
        capacity=2,
        status=JobStatus.PUBLISHED,
    )
    db_session.add(past_job)
    db_session.commit()
    db_session.refresh(past_job)

    res = client.post(f"/api/v1/jobs/{past_job.id}/bookings", headers=student_headers)
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert "already started" in res.json()["detail"]


def test_student_can_view_own_bookings(
    client: TestClient,
    student_headers: dict[str, str],
    published_job: Job,
):
    client.post(f"/api/v1/jobs/{published_job.id}/bookings", headers=student_headers)

    res = client.get("/api/v1/bookings/me", headers=student_headers)
    assert res.status_code == status.HTTP_200_OK
    bookings = res.json()
    assert len(bookings) >= 1
    assert bookings[0]["job_id"] == published_job.id
    assert bookings[0]["job"]["title"] == published_job.title


def test_employer_cannot_inspect_other_employer_bookings(
    client: TestClient,
    db_session: Session,
    published_job: Job,
):
    # Another employer
    other_employer = User(
        name="Other Employer",
        email="other_employer@example.com",
        password_hash=get_password_hash("Pass123!"),
        role=UserRole.EMPLOYER,
        is_active=True,
        is_approved=True,
    )
    db_session.add(other_employer)
    db_session.commit()
    db_session.refresh(other_employer)

    other_token = create_access_token(
        other_employer.id, extra_claims={"role": "employer", "email": other_employer.email}
    )
    other_headers = {"Authorization": f"Bearer {other_token}"}

    # Attempt to view published_job's bookings (which belongs to approved_employer)
    res = client.get(f"/api/v1/employer/jobs/{published_job.id}/bookings", headers=other_headers)
    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert "another employer's vacancy" in res.json()["detail"]


def test_concurrent_booking_cannot_exceed_capacity():
    """Verifies that concurrent booking requests cannot exceed job capacity."""
    setup_session = TestingSessionLocal()
    try:
        # Create an employer
        employer = User(
            name="Concurrent Employer",
            email="conc_emp@example.com",
            password_hash=get_password_hash("Pass123!"),
            role=UserRole.EMPLOYER,
            is_active=True,
            is_approved=True,
        )
        setup_session.add(employer)
        setup_session.commit()
        setup_session.refresh(employer)

        now = datetime.now(UTC)
        job = Job(
            employer_id=employer.id,
            title="Concurrent Slot Job",
            description="Testing race conditions under multi-threaded requests",
            category="IT",
            location="Lab 201",
            pay_amount=20.0,
            pay_unit="per_hour",
            starts_at=now + timedelta(days=2),
            ends_at=now + timedelta(days=2, hours=3),
            capacity=2,
            status=JobStatus.PUBLISHED,
        )
        setup_session.add(job)
        setup_session.commit()
        setup_session.refresh(job)

        # Create 5 distinct students
        tokens = []
        for i in range(5):
            s = User(
                name=f"Concurrent Student {i}",
                email=f"cstudent{i}@example.com",
                password_hash=get_password_hash("Pass123!"),
                role=UserRole.STUDENT,
                is_active=True,
                is_approved=True,
            )
            setup_session.add(s)
            setup_session.commit()
            setup_session.refresh(s)
            tokens.append(create_access_token(s.id, extra_claims={"role": "student", "email": s.email}))

        job_id = job.id
    finally:
        setup_session.close()

    def override_get_db_threadsafe():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db_threadsafe
    test_client = TestClient(app)

    def book_job(token: str):
        headers = {"Authorization": f"Bearer {token}"}
        return test_client.post(f"/api/v1/jobs/{job_id}/bookings", headers=headers)

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        responses = list(executor.map(book_job, tokens))

    app.dependency_overrides.clear()

    status_codes = [r.status_code for r in responses]
    success_count = status_codes.count(status.HTTP_201_CREATED)
    conflict_count = status_codes.count(status.HTTP_409_CONFLICT)

    # Total confirmed bookings in database must equal exactly the capacity (2)
    verify_session = TestingSessionLocal()
    try:
        from app.repositories.booking_repository import BookingRepository

        booking_repo = BookingRepository(verify_session)
        actual_confirmed = booking_repo.count_confirmed_by_job(job_id)
        assert actual_confirmed == 2
        assert success_count == 2
        assert conflict_count == 3
    finally:
        verify_session.close()
