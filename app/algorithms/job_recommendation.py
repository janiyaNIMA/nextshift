from typing import Protocol

from app.models.job import Job
from app.repositories.job_repository import JobRepository


class JobRecommendationStrategy(Protocol):
    """Strategy contract for selecting discoverable jobs for student feed."""

    def recommend_jobs(
        self,
        *,
        job_repo: JobRepository,
        category: str | None = None,
        location: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Job]:
        ...


class AllPublishedJobsStrategy:
    """MVP v0 strategy: same eligible published jobs for every student."""

    def recommend_jobs(
        self,
        *,
        job_repo: JobRepository,
        category: str | None = None,
        location: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Job]:
        return job_repo.list_recommendable_published(
            category=category,
            location=location,
            skip=skip,
            limit=limit,
        )
