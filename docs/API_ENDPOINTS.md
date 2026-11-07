# API Endpoints

Base URL for the application is `/api/v1` unless the server is mounted differently.

## Public health

### `GET /health`
- Purpose: Health check endpoint.
- Authentication: None.
- Response: simple status payload.

## Authentication

### `POST /api/v1/auth/register`
- Purpose: Register a new student or employer account.
- Authentication: None.
- Request body: `UserRegisterRequest`
- Success: `201 Created`
- Response: user profile payload.

### `POST /api/v1/auth/login`
- Purpose: Authenticate a user and return a JWT access token.
- Authentication: None.
- Request body: email and password.
- Success: `200 OK`
- Response: JWT token payload.

### `GET /api/v1/auth/me`
- Purpose: Get the current authenticated user profile.
- Authentication: Bearer JWT required.
- Response: current user payload.

## Jobs and vacancies

### `GET /api/v1/jobs`
- Purpose: List published jobs with optional filters.
- Authentication: None.
- Query parameters:
  - `category` (optional)
  - `location` (optional)
  - `skip` (optional, default `0`)
  - `limit` (optional, default `50`, max `100`)
- Response: array of published jobs.

### `GET /api/v1/jobs/{job_id}`
- Purpose: Fetch details for a published job.
- Authentication: None.
- Response: one job payload.

### `POST /api/v1/jobs`
- Purpose: Create a new job vacancy for the authenticated employer.
- Authentication: Employer JWT required; employer must be approved.
- Request body: `JobCreate`
- Success: `201 Created`
- Response: created job payload.

### `POST /api/v1/jobs/{job_id}/bookings`
- Purpose: Book a published vacancy as a student.
- Authentication: Student JWT required.
- Success: `201 Created`
- Response: booking payload.

### `GET /api/v1/employer/jobs`
- Purpose: List the authenticated employer’s own jobs.
- Authentication: Employer JWT required.
- Query parameters:
  - `skip` (optional)
  - `limit` (optional)
- Response: array of employer jobs.

### `GET /api/v1/employer/jobs/{job_id}/bookings`
- Purpose: List bookings for one of the authenticated employer’s jobs.
- Authentication: Employer JWT required.
- Query parameters:
  - `skip` (optional)
  - `limit` (optional)
- Response: array of booking records for the employer view.

## Bookings

### `GET /api/v1/bookings/me`
- Purpose: View the current student’s own bookings.
- Authentication: Student JWT required.
- Query parameters:
  - `skip` (optional)
  - `limit` (optional)
- Response: array of student bookings.

## Admin

### `GET /api/v1/admin/employers/pending`
- Purpose: List employers awaiting approval.
- Authentication: Admin JWT required.
- Query parameters:
  - `skip` (optional)
  - `limit` (optional)
- Response: list of pending employer profiles.

### `PATCH /api/v1/admin/employers/{user_id}/approve`
- Purpose: Approve a pending employer.
- Authentication: Admin JWT required.
- Response: updated employer profile.

### `GET /api/v1/admin/jobs/pending`
- Purpose: List job postings awaiting moderation.
- Authentication: Admin JWT required.
- Query parameters:
  - `skip` (optional)
  - `limit` (optional)
- Response: list of pending jobs.

### `PATCH /api/v1/admin/jobs/{job_id}/approve`
- Purpose: Approve and publish a pending vacancy.
- Authentication: Admin JWT required.
- Response: updated job payload.

## Authentication model

Most protected routes use a Bearer token in the `Authorization` header:

```http
Authorization: Bearer <access_token>
```

## Typical workflow

1. Register as an employer or student.
2. Admin approves employers and jobs.
3. Approved employers create jobs.
4. Students browse published jobs and submit bookings.
5. Students and employers fetch their own booking/job data via the protected endpoints above.
