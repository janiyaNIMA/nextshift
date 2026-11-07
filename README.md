# NextShift Backend API (Phase 01)

NextShift is a campus part-time-job marketplace backend implemented with **Python 3.12+**, **FastAPI**, **SQLAlchemy 2**, **Alembic**, **Pydantic v2**, and **MySQL** (using **uv** for modern dependency and environment management).

---

## 1. System Architecture & OOP Principles

The project follows a layered domain-driven architecture designed to genuinely demonstrate Object-Oriented Programming (OOP) concepts without artificial complexity:

```text
app/
  ├── main.py                     # FastAPI application factory & exception handling
  ├── cli.py                      # Explicit CLI commands (e.g., admin seeding)
  ├── core/
  │   ├── config.py               # Pydantic Settings & environment variable encapsulation
  │   ├── security.py             # Argon2 hashing & JWT token services
  │   └── exceptions.py           # Domain exception hierarchy (Polymorphism & Inheritance)
  ├── db/
  │   ├── base.py                 # DeclarativeBase & TimestampMixin (Inheritance & Reusability)
  │   └── session.py              # Engine creation & session factory
  ├── models/                     # SQLAlchemy 2 Typed Mappings
  │   ├── user.py                 # User model (roles: student, employer, admin)
  │   ├── job.py                  # Job vacancy model (pending, published, etc.)
  │   └── booking.py              # Booking relationship model with unique constraints
  ├── schemas/                    # Pydantic v2 Data Transfer Objects (Validation & Serialisation)
  │   ├── auth.py
  │   ├── user.py
  │   ├── job.py
  │   └── booking.py
  ├── repositories/               # Data Access Layer (Abstraction & Generics)
  │   ├── base.py                 # Generic BaseRepository[T] with CRUD abstractions
  │   ├── user_repository.py      # UserRepository
  │   ├── job_repository.py       # JobRepository
  │   └── booking_repository.py   # BookingRepository
  ├── services/                   # Business Logic Layer (Encapsulation)
  │   ├── auth_service.py         # Registration & authentication rules
  │   ├── job_service.py          # Vacancy creation & published catalog queries
  │   ├── booking_service.py      # Invariants, capacity checks & concurrency safety
  │   └── admin_service.py        # Employer and vacancy moderation
  └── api/
      ├── deps.py                 # Dependency injection (DB session, RBAC, Current User)
      └── routes/                 # Thin API Controllers
          ├── health.py           # Health check
          ├── auth.py             # Public register, login, me
          ├── jobs.py             # Public catalog, employer jobs, student booking
          ├── bookings.py         # Student own bookings
          └── admin.py            # Admin employer/job approval
alembic/                          # Database schema migrations
tests/                            # Integration test suite (SQLite in-memory)
```

## API Documentation

The current backend endpoint inventory is documented in [docs/API_ENDPOINTS.md](docs/API_ENDPOINTS.md).

### Representation of OOP Principles

1. **Abstraction**:
   - **Repository Pattern (`app.repositories.base.BaseRepository`)**: Abstracts raw database operations behind clean generic CRUD methods (`get_by_id`, `create`, `update`, `delete`), decoupling the business layer from query mechanics.
   - **Service Layer (`app.services.*`)**: Encapsulates and hides business rules, transaction boundaries, and row-locking policies away from API controllers.

2. **Encapsulation**:
   - Internal model attributes, password hashes, and database sessions are strictly encapsulated within their respective services and repositories.
   - Pydantic models (`schemas/`) strictly control the input/output boundaries, preventing sensitive fields like `password_hash` from leaking to clients.

3. **Inheritance**:
   - **Domain Exception Hierarchy (`app.core.exceptions.NextShiftException`)**: `NotFoundException`, `ConflictException`, `ForbiddenException`, `UnauthorizedException`, and `BadRequestException` inherit from `NextShiftException`.
   - **Entity Mixin (`app.db.base.TimestampMixin`)**: Inherited by ORM models to uniformly provide `created_at` timestamp behavior.
   - **Repository Specialization**: `UserRepository`, `JobRepository`, and `BookingRepository` inherit common database behaviors from `BaseRepository`.

4. **Polymorphism**:
   - **Exception Handling**: The global FastAPI exception handler polymorphic treats all domain exceptions as `NextShiftException` while producing the appropriate HTTP status code (`exc.status_code`) and error detail structure dynamically.
   - **Generic Repositories**: Subclasses invoke standard CRUD methods on different database entities uniformly.

---

## 2. Prerequisites & Setup

### Requirements
- [uv](https://docs.astral.sh/uv/) installed
- Python 3.12 or newer
- MySQL Server 8.0+ running

### Environment Configuration
Copy `.env.example` to `.env` and configure your credentials:

```bash
cp .env.example .env
```

Default settings in `.env`:
```ini
PROJECT_NAME="NextShift"
ENVIRONMENT="development"
DEBUG=true
API_V1_STR="/api/v1"

# MySQL Database connection
DATABASE_URL="mysql+pymysql://<user>:<password>@localhost:3306/nextshift?charset=utf8mb4"

# JWT configuration
JWT_SECRET_KEY="your-super-secret-random-key"
JWT_ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Initial Admin Seeding Credentials
FIRST_ADMIN_NAME="System Administrator"
FIRST_ADMIN_EMAIL="admin@nextshift.local"
FIRST_ADMIN_PASSWORD="AdminSecurePassword123!"
```

---

## 3. Database Migrations & Initial Setup

1. **Create MySQL database**:
   ```sql
   CREATE DATABASE IF NOT EXISTS nextshift CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```

2. **Apply Alembic Migrations**:
   ```bash
   uv run alembic upgrade head
   ```

3. **Seed Initial Administrator**:
   ```bash
   uv run python -m app.cli seed-admin
   ```

---

## 4. Running the Development Server

Start the API with automatic reload:

```bash
uv run uvicorn app.main:app --reload
```

Or using the convenience runner:
```bash
uv run python main.py
```

- **Interactive API Documentation (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

---

## 5. Running Tests & Code Quality

### Automated Tests
The test suite runs using an isolated SQLite in-memory database with shared concurrency support, avoiding any mutations on your development database:

```bash
uv run pytest -v
```

### Formatting & Linting
Enforced via `ruff`:

```bash
# Check linting
uv run ruff check .

# Check formatting
uv run ruff format --check .

# Auto-format
uv run ruff format .
```

---

## 6. End-to-End MVP Workflow

1. **Employer Registration**:
   - POST `/api/v1/auth/register` with `role: "employer"`.
   - Employer account is created with `is_approved: false`.

2. **Admin Approval**:
   - Admin logs in: POST `/api/v1/auth/login` using seeded admin credentials.
   - Admin lists pending employers: GET `/api/v1/admin/employers/pending`.
   - Admin approves employer: PATCH `/api/v1/admin/employers/{user_id}/approve`.

3. **Employer Creates Vacancy**:
   - Approved employer logs in and posts: POST `/api/v1/jobs`.
   - Vacancy starts with status `pending` (invisible to students).

4. **Admin Approves Vacancy**:
   - Admin lists pending jobs: GET `/api/v1/admin/jobs/pending`.
   - Admin approves job: PATCH `/api/v1/admin/jobs/{job_id}/approve`.
   - Vacancy status changes to `published`.

5. **Student Browses & Books**:
   - Student registers: POST `/api/v1/auth/register` with `role: "student"` (`is_approved: true`).
   - Student browses published jobs: GET `/api/v1/jobs`.
   - Student books vacancy: POST `/api/v1/jobs/{job_id}/bookings`.
   - Booking is confirmed automatically (`confirmed`). Capacity is decremented safely with concurrency protection.

6. **Viewing Bookings**:
   - Student views own bookings: GET `/api/v1/bookings/me`.
   - Employer views bookings for their job: GET `/api/v1/employer/jobs/{job_id}/bookings`.
