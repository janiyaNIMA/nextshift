# Job Recommendation Algorithm (MVP v0)

## Overview

NextShift uses a replaceable recommendation strategy module at `app/algorithms/job_recommendation.py`.

Current strategy: `AllPublishedJobsStrategy`

- It is intentionally non-personalized.
- Every student sees the same unfiltered job list at the same instant.
- Filters (`category`, `location`) are user-selected, not recommendation personalization.

## Selection Rules

A job is eligible for the student discovery feed only when all conditions are true:

1. `job.status == "published"`
2. Employer account exists and is:
   - role `"employer"`
   - `is_active == true`
   - `is_approved == true`
3. Vacancy is not started/expired:
   - `starts_at > now`
   - `ends_at > now`
4. Remaining capacity exists:
   - confirmed booking count `< capacity`

## Ordering

Because there is no `published_at` column, ordering is:

1. `created_at DESC`
2. `id DESC`

This keeps results deterministic and newest-first.

## Pagination and Filtering

Filtering, ordering, and pagination are applied in SQL in repository layer (`JobRepository.list_recommendable_published`).

Supported optional filters (unchanged from existing API):

- `category` (partial, case-insensitive)
- `location` (partial, case-insensitive)

Pagination params:

- `skip` (offset)
- `limit` (max 100 enforced by route schema)

## Endpoint Using the Strategy

`GET /api/v1/jobs` continues as the discovery feed endpoint.

The service (`JobService.list_published_jobs`) delegates selection to the strategy.

Routes remain thin and unchanged.

## Non-Goals in v0

Not implemented yet:

- skill matching
- location scoring
- ML ranking
- per-student personalized ordering

## Extension Path

Add a new strategy (example `SkillBasedRecommendationStrategy`) implementing the same `JobRecommendationStrategy` protocol, then inject/use it in `JobService` without changing route handlers.
