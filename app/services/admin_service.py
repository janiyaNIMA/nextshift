from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestException, NotFoundException
from app.models.job import Job, JobStatus
from app.models.user import User, UserRole
from app.repositories.job_repository import JobRepository
from app.repositories.user_repository import UserRepository


class AdminService:
    """Service handling administrator moderation of employers and vacancies."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.user_repo = UserRepository(session)
        self.job_repo = JobRepository(session)

    def list_pending_employers(self, skip: int = 0, limit: int = 50) -> list[User]:
        return self.user_repo.list_pending_employers(skip=skip, limit=limit)

    def approve_employer(self, user_id: int) -> User:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundException("Employer not found.")

        if user.role != UserRole.EMPLOYER:
            raise BadRequestException("User is not an employer.")

        user.is_approved = True
        self.user_repo.update(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def list_pending_jobs(self, skip: int = 0, limit: int = 50) -> list[Job]:
        return self.job_repo.list_pending(skip=skip, limit=limit)

    def approve_job(self, job_id: int) -> Job:
        job = self.job_repo.get_by_id(job_id)
        if not job:
            raise NotFoundException("Job vacancy not found.")

        if job.status != JobStatus.PENDING:
            raise BadRequestException("Only pending vacancies can be approved.")

        # Ensure the owner is indeed an employer
        employer = self.user_repo.get_by_id(job.employer_id)
        if not employer or employer.role != UserRole.EMPLOYER:
            raise BadRequestException("Job must be owned by a valid employer.")

        job.status = JobStatus.PUBLISHED
        self.job_repo.update(job)
        self.session.commit()
        self.session.refresh(job)
        return job
