from collections.abc import Generator
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.core.security import create_access_token, get_password_hash
from app.db.base import Base
from app.main import app
from app.models.job import Job, JobStatus
from app.models.user import User, UserRole

# Use SQLite shared-cache in-memory database with StaticPool for fast, isolated testing
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///file:test_nextshift?mode=memory&cache=shared&uri=true"

test_engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False, "timeout": 30},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    bind=test_engine,
)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def create_token(user: User) -> str:
    return create_access_token(
        subject=user.id,
        extra_claims={"role": user.role.value, "email": user.email},
    )


@pytest.fixture
def admin_user(db_session: Session) -> User:
    user = User(
        name="Admin User",
        email="admin@example.com",
        password_hash=get_password_hash("AdminPass123!"),
        role=UserRole.ADMIN,
        is_active=True,
        is_approved=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_headers(admin_user: User) -> dict[str, str]:
    token = create_token(admin_user)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def student_user(db_session: Session) -> User:
    user = User(
        name="Student User",
        email="student@example.com",
        password_hash=get_password_hash("StudentPass123!"),
        role=UserRole.STUDENT,
        is_active=True,
        is_approved=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def student_headers(student_user: User) -> dict[str, str]:
    token = create_token(student_user)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def approved_employer(db_session: Session) -> User:
    user = User(
        name="Approved Employer",
        email="employer_approved@example.com",
        password_hash=get_password_hash("EmployerPass123!"),
        role=UserRole.EMPLOYER,
        is_active=True,
        is_approved=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def employer_headers(approved_employer: User) -> dict[str, str]:
    token = create_token(approved_employer)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def unapproved_employer(db_session: Session) -> User:
    user = User(
        name="Unapproved Employer",
        email="employer_unapproved@example.com",
        password_hash=get_password_hash("EmployerPass123!"),
        role=UserRole.EMPLOYER,
        is_active=True,
        is_approved=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def unapproved_employer_headers(unapproved_employer: User) -> dict[str, str]:
    token = create_token(unapproved_employer)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def published_job(db_session: Session, approved_employer: User) -> Job:
    now = datetime.now(UTC)
    job = Job(
        employer_id=approved_employer.id,
        title="Library Assistant",
        description="Assisting visitors and organizing book inventory",
        category="Library",
        location="Main Campus",
        pay_amount=15.50,
        pay_unit="per_hour",
        starts_at=now + timedelta(days=2),
        ends_at=now + timedelta(days=2, hours=4),
        capacity=2,
        status=JobStatus.PUBLISHED,
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    return job
