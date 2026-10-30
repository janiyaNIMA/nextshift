from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.booking import Booking, BookingStatus
from app.repositories.base import BaseRepository


class BookingRepository(BaseRepository[Booking]):
    def __init__(self, session: Session) -> None:
        super().__init__(Booking, session)

    def get_by_job_and_student(self, job_id: int, student_id: int) -> Booking | None:
        stmt = select(Booking).where(
            Booking.job_id == job_id,
            Booking.student_id == student_id,
        )
        return self.session.scalars(stmt).first()

    def count_confirmed_by_job(self, job_id: int) -> int:
        stmt = select(func.count(Booking.id)).where(
            Booking.job_id == job_id,
            Booking.status == BookingStatus.CONFIRMED,
        )
        count = self.session.scalar(stmt)
        return int(count or 0)

    def list_by_student(self, student_id: int, skip: int = 0, limit: int = 50) -> list[Booking]:
        stmt = (
            select(Booking)
            .options(joinedload(Booking.job))
            .where(Booking.student_id == student_id)
            .order_by(Booking.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(self.session.scalars(stmt).unique().all())

    def list_by_job(self, job_id: int, skip: int = 0, limit: int = 50) -> list[Booking]:
        stmt = (
            select(Booking)
            .options(joinedload(Booking.student))
            .where(Booking.job_id == job_id)
            .order_by(Booking.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(self.session.scalars(stmt).unique().all())
