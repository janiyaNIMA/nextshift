from sqlalchemy.orm import Session

from app.core.exceptions import (
    BadRequestException,
    ForbiddenException,
    NotFoundException,
)
from app.models.job import Job, JobStatus
from app.models.user import User, UserRole
from app.repositories.booking_repository import BookingRepository
from app.repositories.job_repository import JobRepository
from app.schemas.job import JobCreate, JobResponse


class JobService:
    """Service encapsulating job vacancy management and querying."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.job_repo = JobRepository(session)
        self.booking_repo = BookingRepository(session)

    def create_job(self, employer: User, job_in: JobCreate) -> Job:
        if employer.role != UserRole.EMPLOYER:
            raise ForbiddenException("Only employers can create job vacancies.")

        if not employer.is_approved:
            raise ForbiddenException("Your employer account is pending administrator approval.")

        if job_in.ends_at <= job_in.starts_at:
            raise BadRequestException("Job end time must be after start time.")

        if job_in.capacity < 1:
            raise BadRequestException("Job capacity must be at least 1.")

        if job_in.pay_amount < 0:
            raise BadRequestException("Pay amount cannot be negative.")

        job = Job(
            employer_id=employer.id,
            title=job_in.title.strip(),
            description=job_in.description.strip(),
            category=job_in.category.strip(),
            location=job_in.location.strip(),
            pay_amount=job_in.pay_amount,
            pay_unit=job_in.pay_unit.strip(),
            starts_at=job_in.starts_at,
            ends_at=job_in.ends_at,
            capacity=job_in.capacity,
            status=JobStatus.PENDING,
        )
        self.job_repo.create(job)
        self.session.commit()
        self.session.refresh(job)
        return job

    def list_published_jobs(
        self,
        category: str | None = None,
        location: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[JobResponse]:
        jobs = self.job_repo.list_published(category=category, location=location, skip=skip, limit=limit)
        results: list[JobResponse] = []
        for job in jobs:
            booked = self.booking_repo.count_confirmed_by_job(job.id)
            res = JobResponse.model_validate(job)
            res.remaining_capacity = max(0, job.capacity - booked)
            results.append(res)
        return results

    def get_published_job(self, job_id: int) -> JobResponse:
        job = self.job_repo.get_published_by_id(job_id)
        if not job:
            raise NotFoundException("Published vacancy not found.")
        booked = self.booking_repo.count_confirmed_by_job(job.id)
        res = JobResponse.model_validate(job)
        res.remaining_capacity = max(0, job.capacity - booked)
        return res

    def list_employer_jobs(self, employer_id: int, skip: int = 0, limit: int = 50) -> list[JobResponse]:
        jobs = self.job_repo.list_by_employer(employer_id=employer_id, skip=skip, limit=limit)
        results: list[JobResponse] = []
        for job in jobs:
            booked = self.booking_repo.count_confirmed_by_job(job.id)
            res = JobResponse.model_validate(job)
            res.remaining_capacity = max(0, job.capacity - booked)
            results.append(res)
        return results
