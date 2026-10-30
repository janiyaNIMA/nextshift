import threading
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
)
from app.models.booking import Booking, BookingStatus
from app.models.job import JobStatus
from app.models.user import User, UserRole
from app.repositories.booking_repository import BookingRepository
from app.repositories.job_repository import JobRepository


class BookingService:
    """Service handling job booking invariants, row locking, and student/employer booking views."""

    _lock = threading.Lock()

    def __init__(self, session: Session) -> None:
        self.session = session
        self.job_repo = JobRepository(session)
        self.booking_repo = BookingRepository(session)

    def book_job(self, student: User, job_id: int) -> Booking:
        if student.role != UserRole.STUDENT:
            raise ForbiddenException("Only students can book job vacancies.")

        # Application mutex + DB row-level locking provides robust race-condition protection
        # across threads and multi-process MySQL transactions.
        with self._lock:
            # Row-level lock within the current transaction ensures strict serialized capacity checks
            job = self.job_repo.get_with_lock(job_id)
            if not job or job.status != JobStatus.PUBLISHED:
                raise NotFoundException("Published vacancy not found.")

            # Start time invariant: vacancy must be in the future
            now = datetime.now(UTC)
            job_start = job.starts_at
            if job_start.tzinfo is None:
                job_start = job_start.replace(tzinfo=UTC)

            if job_start <= now:
                raise BadRequestException("Cannot book a vacancy that has already started.")

            # Duplicate booking check
            existing = self.booking_repo.get_by_job_and_student(job_id=job.id, student_id=student.id)
            if existing:
                raise ConflictException("You have already booked this vacancy.")

            # Capacity check
            confirmed_count = self.booking_repo.count_confirmed_by_job(job.id)
            if confirmed_count >= job.capacity:
                raise ConflictException("This vacancy has reached its maximum booking capacity.")

            booking = Booking(
                job_id=job.id,
                student_id=student.id,
                status=BookingStatus.CONFIRMED,
            )
            self.booking_repo.create(booking)
            self.session.commit()
            return booking

    def get_student_bookings(self, student_id: int, skip: int = 0, limit: int = 50) -> list[Booking]:
        return self.booking_repo.list_by_student(student_id=student_id, skip=skip, limit=limit)

    def get_job_bookings_for_employer(
        self,
        employer_id: int,
        job_id: int,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Booking]:
        job = self.job_repo.get_by_id(job_id)
        if not job:
            raise NotFoundException("Job vacancy not found.")

        # Prevent employers from inspecting other employers' jobs/bookings
        if job.employer_id != employer_id:
            raise ForbiddenException("You cannot view bookings for another employer's vacancy.")

        return self.booking_repo.list_by_job(job_id=job_id, skip=skip, limit=limit)
