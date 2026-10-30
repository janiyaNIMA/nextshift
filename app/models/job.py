from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.booking import Booking
    from app.models.user import User


class JobStatus(str, Enum):
    PENDING = "pending"
    PUBLISHED = "published"
    REJECTED = "rejected"
    CLOSED = "closed"


class Job(Base, TimestampMixin):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    employer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    pay_amount: Mapped[float] = mapped_column(Float, nullable=False)
    pay_unit: Mapped[str] = mapped_column(String(50), nullable=False, default="per_hour")
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[JobStatus] = mapped_column(
        SQLEnum(JobStatus, native_enum=False, length=50),
        nullable=False,
        default=JobStatus.PENDING,
        index=True,
    )

    # Relationships
    employer: Mapped["User"] = relationship("User", back_populates="jobs")
    bookings: Mapped[list["Booking"]] = relationship("Booking", back_populates="job", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Job id={self.id} title={self.title!r} status={self.status}>"
