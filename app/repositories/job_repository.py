from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.job import Job, JobStatus
from app.models.user import User, UserRole
from app.models.booking import Booking, BookingStatus
from app.repositories.base import BaseRepository


class JobRepository(BaseRepository[Job]):
    def __init__(self, session: Session) -> None:
        super().__init__(Job, session)

    def list_published(
        self,
        category: str | None = None,
        location: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Job]:
        stmt = select(Job).where(Job.status == JobStatus.PUBLISHED)
        if category:
            stmt = stmt.where(Job.category.ilike(f"%{category.strip()}%"))
        if location:
            stmt = stmt.where(Job.location.ilike(f"%{location.strip()}%"))
        stmt = stmt.order_by(Job.starts_at.asc()).offset(skip).limit(limit)
        return list(self.session.scalars(stmt).all())

    def list_recommendable_published(
        self,
        category: str | None = None,
        location: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Job]:
        now = datetime.now(UTC)

        confirmed_count_subquery = (
            select(
                Booking.job_id.label("job_id"),
                func.count(Booking.id).label("confirmed_count"),
            )
            .where(Booking.status == BookingStatus.CONFIRMED)
            .group_by(Booking.job_id)
            .subquery()
        )

        stmt = (
            select(Job)
            .join(User, User.id == Job.employer_id)
            .outerjoin(confirmed_count_subquery, confirmed_count_subquery.c.job_id == Job.id)
            .where(
                Job.status == JobStatus.PUBLISHED,
                User.role == UserRole.EMPLOYER,
                User.is_active.is_(True),
                User.is_approved.is_(True),
                Job.starts_at > now,
                Job.ends_at > now,
                func.coalesce(confirmed_count_subquery.c.confirmed_count, 0) < Job.capacity,
            )
        )

        if category:
            stmt = stmt.where(Job.category.ilike(f"%{category.strip()}%"))
        if location:
            stmt = stmt.where(Job.location.ilike(f"%{location.strip()}%"))

        stmt = stmt.order_by(Job.created_at.desc(), Job.id.desc()).offset(skip).limit(limit)
        return list(self.session.scalars(stmt).all())

    def get_published_by_id(self, job_id: int) -> Job | None:
        stmt = select(Job).where(Job.id == job_id, Job.status == JobStatus.PUBLISHED)
        return self.session.scalars(stmt).first()

    def list_by_employer(self, employer_id: int, skip: int = 0, limit: int = 50) -> list[Job]:
        stmt = (
            select(Job).where(Job.employer_id == employer_id).order_by(Job.created_at.desc()).offset(skip).limit(limit)
        )
        return list(self.session.scalars(stmt).all())

    def list_pending(self, skip: int = 0, limit: int = 50) -> list[Job]:
        stmt = (
            select(Job).where(Job.status == JobStatus.PENDING).order_by(Job.created_at.asc()).offset(skip).limit(limit)
        )
        return list(self.session.scalars(stmt).all())

    def get_with_lock(self, job_id: int) -> Job | None:
        """Locks the job row within an active transaction for concurrency safety."""
        stmt = select(Job).where(Job.id == job_id).with_for_update()
        return self.session.scalars(stmt).first()
