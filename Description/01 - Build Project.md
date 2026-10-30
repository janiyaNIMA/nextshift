# Antigravity Initial Prompt — NextShift Backend (Phase 01)

You are a senior Python backend engineer. Initialize a clean, maintainable backend for **NextShift**, a campus part-time-job marketplace, using **Python, FastAPI, uv, SQLAlchemy 2, Alembic, Pydantic v2, and MySQL**.

## Product context
NextShift has two public user roles:
- **Student**: register, log in, browse published vacancies, book an available vacancy, view own bookings.
- **Employer**: register, log in, create vacancies, view own vacancies and their bookings.

There is also a restricted **Admin** role for approving employer accounts and individual job vacancies. Do **not** provide public admin registration.

The MVP workflow is:
Employer registers → admin approves employer → employer creates vacancy → admin approves vacancy → student browses published vacancies → student books vacancy → booking is confirmed automatically.

## Objective
Implement **Phase 01: a runnable API foundation and basic end-to-end MVP endpoints**. Keep code modular, readable, and suitable for demonstrating OOP principles in a university project. Do not build the frontend, notifications, ratings, payments, messaging, or recommendation engine yet.

## Tooling and setup
- Use `uv` for project/dependency management. Initialize with `uv init` if needed; use `uv add` and `uv add --dev` for dependencies.
- Use Python 3.12+; FastAPI with Uvicorn, SQLAlchemy 2 ORM, Alembic, Pydantic v2, pydantic-settings, PyMySQL, and pytest/httpx.
- Configure database credentials and JWT signing secret via `.env` and `.env.example`; never commit `.env`.
- Use `uv run` for all commands, e.g. `uv run uvicorn app.main:app --reload`.
- Provide a `.gitignore`, clear `README.md`, and reproducible `uv.lock`.
- Use a MySQL database named `nextshift` (configurable by `DATABASE_URL`).
- Do not run destructive database commands or silently modify an existing database.

## Architecture
Use a layered structure:

```text
app/
  main.py
  core/config.py
  core/security.py
  db/base.py
  db/session.py
  models/{user,job,booking}.py
  schemas/{auth,user,job,booking}.py
  api/deps.py
  api/routes/{health,auth,jobs,bookings,admin}.py
  services/{auth_service,job_service,booking_service,admin_service}.py
  repositories/
alembic/
tests/
.env.example
.gitignore
pyproject.toml
README.md
```

Keep API routers thin; implement business rules in service classes and persistence in repositories. Use SQLAlchemy 2 typed mappings. Explain in README how inheritance, encapsulation, abstraction and polymorphism are genuinely represented (do not force meaningless inheritance).

## Data model
- `users`: id, name, email (unique), password_hash, role (`student`, `employer`, `admin`), is_active, is_approved, created_at.
- `jobs`: id, employer_id (FK users), title, description, category, location, pay_amount, pay_unit, starts_at, ends_at, capacity (default 1), status (`pending`, `published`, `rejected`, `closed`), created_at.
- `bookings`: id, job_id (FK jobs), student_id (FK users), status (`confirmed`, `cancelled`), created_at; unique `(job_id, student_id)` for MVP.

Use timezone-aware UTC timestamps in the API; store consistently in MySQL. Add indexes on jobs status, employer_id and bookings student_id.

## Authentication and permissions
- Passwords must be securely hashed (Argon2 preferred); never store plaintext passwords.
- Use JWT bearer access tokens with expiry and configurable signing secret.
- Public registration only permits student or employer roles. Students can become active immediately; employers require admin approval before posting jobs.
- Authenticate via email/password; reject disabled users.
- Enforce role-based authorization on every protected endpoint. A user must never edit/read another user's private records.
- Seed the first admin via an explicit CLI command that reads credentials from environment variables, never through an unauthenticated endpoint or hardcoded default password.

## API endpoints (v1)
Implement these routes with request/response Pydantic schemas, validation, appropriate HTTP codes, and OpenAPI docs:

| Method | Path | Purpose | Access |
|---|---|---|---|
| GET | `/health` | Health check | Public |
| POST | `/api/v1/auth/register` | Register student/employer | Public |
| POST | `/api/v1/auth/login` | Return access token | Public |
| GET | `/api/v1/auth/me` | Current user profile | Authenticated |
| GET | `/api/v1/jobs` | List published jobs; optional category/location filters and pagination | Public |
| GET | `/api/v1/jobs/{job_id}` | View published job | Public |
| POST | `/api/v1/jobs` | Create pending vacancy | Approved employer |
| GET | `/api/v1/employer/jobs` | List own vacancies | Employer |
| GET | `/api/v1/employer/jobs/{job_id}/bookings` | List bookings for own job | Employer |
| POST | `/api/v1/jobs/{job_id}/bookings` | Book published vacancy | Student |
| GET | `/api/v1/bookings/me` | View own bookings | Student |
| GET | `/api/v1/admin/employers/pending` | Pending employer approvals | Admin |
| PATCH | `/api/v1/admin/employers/{user_id}/approve` | Approve employer | Admin |
| GET | `/api/v1/admin/jobs/pending` | Pending job approvals | Admin |
| PATCH | `/api/v1/admin/jobs/{job_id}/approve` | Publish approved job | Admin |

Business rules:
1. Only approved employers can create jobs.
2. New jobs always start as `pending`; students see only `published` jobs.
3. Admin approval moves a pending job to `published`; only an employer-owned job can be approved.
4. A student can book only a published job whose start time is in the future and which has remaining capacity.
5. Reject duplicate bookings; use a transaction and row locking or another safe strategy to prevent overbooking under concurrent requests.
6. Student bookings become `confirmed` immediately (no separate employer approval).
7. Validate `ends_at > starts_at`, `capacity >= 1`, and nonnegative pay.
8. Return consistent error JSON with meaningful status codes (400/401/403/404/409/422).
9. Avoid exposing password hashes or private student information in public responses.
10. For MVP, cancellations and rebooking are **out of scope**; preserve a booking status column for future expansion.

## Implementation sequence
1. Inspect the current repository first; preserve existing work and report what is already present.
2. Initialize uv project and dependencies.
3. Add settings, app entrypoint, database engine/session, and health endpoint.
4. Define SQLAlchemy models and create the first Alembic migration.
5. Implement password hashing, JWT auth, registration/login and current-user dependency.
6. Implement employer/job approval, job publishing, listing and detail.
7. Implement student booking with capacity safety and employer/own booking views.
8. Write tests and README instructions.
9. Run formatting/linting, tests, and a startup smoke test; fix failures.

## Testing acceptance criteria
Include tests for:
- student and employer registration; duplicate email
- login success/failure and JWT protection
- student cannot create a job; unapproved employer cannot create a job
- employer job starts pending and is invisible publicly
- only admin can approve employer/job
- approved job appears in public list
- student can book; employer cannot book
- duplicate booking and full-capacity booking are rejected
- concurrent booking requests cannot exceed capacity
- employers cannot inspect other employers' bookings
- invalid dates, capacity, and pay are rejected

Use a separate test database; never run tests against the development database. Prefer integration tests that exercise the API and database behavior.

## Deliverables and working style
- Make actual changes to the repository; don't just describe the implementation.
- Work incrementally and keep modules small.
- Do not introduce unnecessary infrastructure (Docker, Celery, Redis, microservices) in Phase 01.
- After implementing, report files created, commands executed, test results, remaining limitations, and the exact next command to run.
- If MySQL is not available, complete the code and migrations, run tests that can safely run, and explicitly report what could not be verified.
- Ask only when a blocking decision is unavoidable; otherwise follow the rules in this prompt.
