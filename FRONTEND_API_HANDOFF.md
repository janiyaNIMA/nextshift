# NextShift Backend API Handoff for Frontend Team

This document is the implementation-aligned API contract for frontend integration.

## 1) Quick Start for Frontend Team

- API base URL (local): `http://localhost:8000`
- API version prefix: `/api/v1`
- OpenAPI JSON: `/api/v1/openapi.json`
- Swagger docs: `/docs`

Final API base path for most endpoints:

`http://localhost:8000/api/v1`

Health endpoint is outside the version prefix:

`GET http://localhost:8000/health`

---

## 2) Authentication Model

Auth uses JWT Bearer tokens.

1. User logs in via `POST /api/v1/auth/login`
2. API returns:
   - `access_token`
   - `token_type` (always `bearer`)
3. Frontend sends token on protected routes:

`Authorization: Bearer <access_token>`

### Token facts

- No refresh token endpoint exists yet.
- Token expiration is controlled by backend config (`ACCESS_TOKEN_EXPIRE_MINUTES`, default 60).

---

## 3) Role & Approval Rules (Important)

Roles in system:

- `student`
- `employer`
- `admin`

Public registration only allows:

- `student`
- `employer`

Approval behavior:

- `student` is immediately approved (`is_approved = true`)
- `employer` is pending approval (`is_approved = false`) until admin approves

### Capability Matrix

| Feature | Public | Student | Employer (unapproved) | Employer (approved) | Admin |
|---|---|---|---|---|---|
| Register / Login | Yes | Yes | Yes | Yes | Yes |
| View published jobs | Yes | Yes | Yes | Yes | Yes |
| Create job | No | No | No (403) | Yes | No |
| Book job | No | Yes | No | No | No |
| View own bookings | No | Yes | No | No | No |
| View own employer jobs | No | No | Yes | Yes | No |
| View bookings for own job | No | No | Yes | Yes | No |
| Approve employers/jobs | No | No | No | No | Yes |

---

## 4) Common Response Shapes

### Success

Standard JSON objects/arrays based on endpoint response model.

### Domain error format (custom business errors)

```json
{
  "detail": "Human-readable error message"
}
```

Sometimes with extra data:

```json
{
  "detail": "Human-readable error message",
  "data": {}
}
```

### Validation error format (FastAPI/Pydantic)

```json
{
  "detail": [
    {
      "type": "...",
      "loc": ["body", "field_name"],
      "msg": "...",
      "input": "..."
    }
  ]
}
```

### Typical status codes used

- `200` OK
- `201` Created
- `400` Bad Request (business rule violation)
- `401` Unauthorized (missing/invalid token or invalid credentials)
- `403` Forbidden (role/permission/approval restrictions)
- `404` Not Found
- `409` Conflict (duplicate/unique conflict)
- `422` Unprocessable Content (schema validation)

---

## 5) Data Models for Frontend

### Auth

#### LoginRequest

```json
{
  "email": "user@example.com",
  "password": "string"
}
```

#### Token

```json
{
  "access_token": "jwt-string",
  "token_type": "bearer"
}
```

### User

#### UserRegisterRequest

```json
{
  "name": "Full Name",
  "email": "user@example.com",
  "password": "Min8Chars",
  "role": "student"
}
```

`role` allowed values: `student`, `employer`

#### UserResponse

```json
{
  "id": 1,
  "name": "Full Name",
  "email": "user@example.com",
  "role": "student",
  "is_active": true,
  "is_approved": true,
  "created_at": "2026-10-30T10:00:00Z"
}
```

### Job

#### JobCreate

```json
{
  "title": "IT Lab Assistant",
  "description": "Help students with lab computer troubleshooting",
  "category": "Technology",
  "location": "Computer Center",
  "pay_amount": 18.0,
  "pay_unit": "per_hour",
  "starts_at": "2026-11-05T09:00:00Z",
  "ends_at": "2026-11-05T13:00:00Z",
  "capacity": 3
}
```

Rules:

- `ends_at` must be strictly after `starts_at`
- `capacity >= 1`
- `pay_amount >= 0`

#### JobResponse

```json
{
  "id": 10,
  "employer_id": 3,
  "title": "IT Lab Assistant",
  "description": "Help students with lab computer troubleshooting",
  "category": "Technology",
  "location": "Computer Center",
  "pay_amount": 18.0,
  "pay_unit": "per_hour",
  "starts_at": "2026-11-05T09:00:00Z",
  "ends_at": "2026-11-05T13:00:00Z",
  "capacity": 3,
  "remaining_capacity": 2,
  "status": "published",
  "created_at": "2026-10-30T10:00:00Z"
}
```

`status` values: `pending`, `published`, `rejected`, `closed`

### Booking

#### BookingResponse

```json
{
  "id": 20,
  "job_id": 10,
  "student_id": 4,
  "status": "confirmed",
  "created_at": "2026-10-30T10:10:00Z"
}
```

`status` values: `confirmed`, `cancelled`

#### StudentBookingResponse

```json
{
  "id": 20,
  "job_id": 10,
  "student_id": 4,
  "status": "confirmed",
  "created_at": "2026-10-30T10:10:00Z",
  "job": {
    "id": 10,
    "employer_id": 3,
    "title": "IT Lab Assistant",
    "description": "...",
    "category": "Technology",
    "location": "Computer Center",
    "pay_amount": 18.0,
    "pay_unit": "per_hour",
    "starts_at": "2026-11-05T09:00:00Z",
    "ends_at": "2026-11-05T13:00:00Z",
    "capacity": 3,
    "remaining_capacity": 2,
    "status": "published",
    "created_at": "2026-10-30T10:00:00Z"
  }
}
```

#### EmployerBookingResponse

```json
{
  "id": 20,
  "job_id": 10,
  "student_id": 4,
  "status": "confirmed",
  "created_at": "2026-10-30T10:10:00Z",
  "student": {
    "id": 4,
    "name": "Student User",
    "email": "student@example.com"
  }
}
```

---

## 6) Endpoint-by-Endpoint Contract

All paths below are relative to `/api/v1` unless otherwise noted.

## 6.1 Health

### GET /health (outside /api/v1)

- Auth: none
- Response 200:

```json
{
  "status": "ok",
  "app": "NextShift"
}
```

---

## 6.2 Auth

### POST /auth/register

- Auth: none
- Body: `UserRegisterRequest`
- Response: `201 Created`, `UserResponse`
- Notes:
  - Duplicate email -> `409`
  - Employer registers as pending approval

### POST /auth/login

- Auth: none
- Body: `LoginRequest`
- Response: `200`, `Token`
- Notes:
  - Invalid credentials -> `401`
  - Inactive account -> `403`

### GET /auth/me

- Auth: Bearer token required
- Response: `200`, `UserResponse`
- Notes:
  - Missing token -> `401`

---

## 6.3 Jobs & Vacancies

### GET /jobs

- Auth: none
- Query params:
  - `category` (optional string)
  - `location` (optional string)
  - `skip` (default 0, min 0)
  - `limit` (default 50, min 1, max 100)
- Response: `200`, `JobResponse[]`

### GET /jobs/{job_id}

- Auth: none
- Response: `200`, `JobResponse`
- Errors:
  - Not found or not published -> `404`

### POST /jobs

- Auth: Bearer token, employer role, and approved employer required
- Body: `JobCreate`
- Response: `201`, `JobResponse`
- Notes:
  - New job starts as `pending`
- Errors:
  - Not employer or not approved -> `403`
  - Rule violations -> `400` or `422`

### GET /employer/jobs

- Auth: Bearer token, employer role required
- Query params: `skip`, `limit`
- Response: `200`, `JobResponse[]`

### GET /employer/jobs/{job_id}/bookings

- Auth: Bearer token, employer role required
- Query params: `skip`, `limit`
- Response: `200`, `EmployerBookingResponse[]`
- Errors:
  - Job not found -> `404`
  - Job belongs to different employer -> `403`

---

## 6.4 Bookings

### POST /jobs/{job_id}/bookings

- Auth: Bearer token, student role required
- Body: none
- Response: `201`, `BookingResponse`
- Errors:
  - Job not found or not published -> `404`
  - Already booked same job -> `409`
  - Capacity reached -> `409`
  - Job already started -> `400`

### GET /bookings/me

- Auth: Bearer token, student role required
- Query params: `skip`, `limit`
- Response: `200`, `StudentBookingResponse[]`

---

## 6.5 Admin

### GET /admin/employers/pending

- Auth: Bearer token, admin role required
- Query params: `skip`, `limit`
- Response: `200`, `UserResponse[]`

### PATCH /admin/employers/{user_id}/approve

- Auth: Bearer token, admin role required
- Body: none
- Response: `200`, `UserResponse`
- Errors:
  - Employer not found -> `404`
  - User exists but is not employer -> `400`

### GET /admin/jobs/pending

- Auth: Bearer token, admin role required
- Query params: `skip`, `limit`
- Response: `200`, `JobResponse[]`

### PATCH /admin/jobs/{job_id}/approve

- Auth: Bearer token, admin role required
- Body: none
- Response: `200`, `JobResponse`
- Errors:
  - Job not found -> `404`
  - Job not pending -> `400`
  - Job owner invalid employer -> `400`

---

## 7) Frontend Integration Flows

## 7.1 Student flow

1. Register as student via `POST /auth/register`
2. Login via `POST /auth/login`
3. Browse jobs via `GET /jobs`
4. Book via `POST /jobs/{job_id}/bookings`
5. View own bookings via `GET /bookings/me`

## 7.2 Employer flow

1. Register as employer via `POST /auth/register`
2. Login via `POST /auth/login`
3. Before approval, creating jobs returns `403`
4. After admin approval, create job via `POST /jobs`
5. View own jobs/bookings via employer endpoints

## 7.3 Admin flow

1. Login with admin credentials via `POST /auth/login`
2. Review pending employers/jobs
3. Approve employers/jobs with admin PATCH endpoints

---

## 8) Frontend Implementation Notes

- Save JWT token securely in frontend state/storage per your security policy.
- Attach `Authorization` header for all protected calls.
- Treat `401` as session/auth failure (redirect to login).
- Treat `403` as permission/approval issue (show role-appropriate message).
- Treat `409` as business conflict with user-readable message.
- Parse both domain errors (`detail: string`) and validation errors (`detail: []`).
- Use ISO datetime parsing for all `*_at` fields.

---

## 9) Known Development Caveat

If login fails at validation with email domains like `.local`, the strict email validator may reject special-use domains.

For smoother frontend QA, use normal domains like `example.com` for test users.
