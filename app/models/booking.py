from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.job import Job
    from app.models.user import User


class BookingStatus(str, Enum):
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


class Booking(Base, TimestampMixin):
    __tablename__ = "bookings"
    __table_args__ = (UniqueConstraint("job_id", "student_id", name="uq_bookings_job_student"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), index=True, nullable=False)
    student_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    status: Mapped[BookingStatus] = mapped_column(
        SQLEnum(BookingStatus, native_enum=False, length=50),
        nullable=False,
        default=BookingStatus.CONFIRMED,
    )

    # Relationships
    job: Mapped["Job"] = relationship("Job", back_populates="bookings")
    student: Mapped["User"] = relationship("User", back_populates="bookings")

    def __repr__(self) -> str:
        return f"<Booking id={self.id} job_id={self.job_id} student_id={self.student_id} status={self.status}>"
