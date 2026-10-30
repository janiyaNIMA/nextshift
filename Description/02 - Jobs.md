# Antigravity Prompt — NextShift Job Recommendation v0

## Context
Modify the existing NextShift backend (Python, FastAPI, SQLAlchemy, MySQL, uv). Students browse vacancies posted by employers/shops. Employer accounts and each vacancy require admin approval.

## Goal
Create a **separate, replaceable recommendation algorithm module**. In MVP version 0, show **all eligible published job vacancies to every student**, newest first. Do not implement personalized ranking, machine learning, skill matching, or location scoring yet.

## Tasks
1. Inspect the existing repository and reuse its models, routes, services, pagination, and naming conventions. Do not overwrite working code or duplicate endpoints.
2. Create `app/algorithms/job_recommendation.py` (adjust path to existing conventions) and an `__init__.py`. Define a typed `JobRecommendationStrategy` interface (e.g., an abstract base class or Protocol) and `AllPublishedJobsStrategy` implementation. Keep selection rules in this module; database queries belong in the repository layer.
3. Eligibility: job status is `published`; associated employer has role `employer`, is active and approved; vacancy is not expired or already started; booking capacity remains available. Follow existing time/capacity policies if already defined, and document deviations. Do not show pending, rejected, closed, or unapproved vacancies.
4. Ordering: `published_at DESC, id DESC` if `published_at` exists; otherwise `created_at DESC, id DESC`. Apply filtering, ordering and pagination in SQL rather than loading all jobs into memory.
5. Use the existing `GET /api/v1/jobs` feed for discovery. If a dedicated student feed already exists, reuse it instead; do not create redundant endpoints. Preserve existing optional user-selected filters (e.g., category/location), response schemas, pagination, and job detail endpoint. The **unfiltered** feed should be identical for all students at the same instant.
6. Have the job service call the strategy. API routes must remain thin. Make it straightforward to introduce a future `SkillBasedRecommendationStrategy` without changing route handlers.
7. Do not alter authentication, booking, employer approval, or admin approval behavior. Never expose unpublished jobs.
8. Add `docs/JOB_RECOMMENDATION.md` describing the algorithm, rules, ordering, limitations, and how future personalized strategies could replace it.
9. Add tests in `tests/test_job_recommendation.py` (or consistent existing location): eligible jobs visible to all students, pending/rejected/closed jobs hidden, unapproved employers hidden, expired jobs hidden, full jobs excluded from bookable feed, newest-first stable ordering, pagination, optional filters, empty feed, no duplicates, and no authorization regression.

## Suggested structure
```text
app/
  algorithms/
    __init__.py
    job_recommendation.py
  services/job_service.py
  repositories/...
  api/routes/jobs.py

docs/JOB_RECOMMENDATION.md
tests/test_job_recommendation.py
```

## Conceptual algorithm (pseudocode)
```python
def recommend_jobs(student, page, page_size, filters=None):
    # No student-specific ranking or filtering in v0.
    jobs = query_eligible_jobs(
        status="published",
        employer_active=True,
        employer_approved=True,
        future_start=True,
        has_remaining_capacity=True,
        filters=filters,
    )
    return jobs.order_by("published_at DESC", "id DESC").paginate(page, page_size)
```
Adapt this pseudocode to the real models; do not invent unsupported columns.

## Acceptance criteria
- An approved eligible vacancy appears in the student feed.
- Every student sees the same eligible vacancies without personalized ordering.
- Unapproved, pending, rejected, closed, expired, or full vacancies are not offered as bookable jobs.
- Results are paginated, deterministic, and newest first.
- Recommendation logic is isolated in its own file.
- Existing features and tests remain functional.

## Execution
Implement actual code changes incrementally. Run `uv run pytest` and any existing lint commands. Report files changed, endpoint used, test results, and assumptions. If the database is unavailable, state exactly what could not be tested. Do not add frontend or ML dependencies.
