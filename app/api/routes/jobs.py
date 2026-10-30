from fastapi import APIRouter, Query, status

from app.api.deps import (
    DbSession,
    RequireApprovedEmployer,
    RequireEmployer,
    RequireStudent,
)
from app.schemas.booking import BookingResponse, EmployerBookingResponse
from app.schemas.job import JobCreate, JobResponse
from app.services.booking_service import BookingService
from app.services.job_service import JobService

router = APIRouter(tags=["Jobs & Vacancies"])


@router.get(
    "/jobs",
    response_model=list[JobResponse],
    summary="List published job vacancies with optional filters",
)
def list_published_jobs(
    db: DbSession,
    category: str | None = Query(None, description="Filter by job category"),
    location: str | None = Query(None, description="Filter by location"),
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(50, ge=1, le=100, description="Limit for pagination"),
):
    job_service = JobService(db)
    return job_service.list_published_jobs(
        category=category,
        location=location,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/jobs/{job_id}",
    response_model=JobResponse,
    summary="View details of a published job vacancy",
)
def get_published_job(job_id: int, db: DbSession):
    job_service = JobService(db)
    return job_service.get_published_job(job_id)


@router.post(
    "/jobs",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new job vacancy (starts as pending)",
)
def create_job(
    job_in: JobCreate,
    current_employer: RequireApprovedEmployer,
    db: DbSession,
):
    job_service = JobService(db)
    created = job_service.create_job(employer=current_employer, job_in=job_in)
    return created


@router.post(
    "/jobs/{job_id}/bookings",
    response_model=BookingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Book a published vacancy (Student)",
)
def book_vacancy(
    job_id: int,
    current_student: RequireStudent,
    db: DbSession,
):
    booking_service = BookingService(db)
    booking = booking_service.book_job(student=current_student, job_id=job_id)
    return booking


@router.get(
    "/employer/jobs",
    response_model=list[JobResponse],
    summary="List employer's own job vacancies",
)
def list_employer_jobs(
    current_employer: RequireEmployer,
    db: DbSession,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    job_service = JobService(db)
    return job_service.list_employer_jobs(
        employer_id=current_employer.id,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/employer/jobs/{job_id}/bookings",
    response_model=list[EmployerBookingResponse],
    summary="List bookings for employer's own vacancy",
)
def list_employer_job_bookings(
    job_id: int,
    current_employer: RequireEmployer,
    db: DbSession,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    booking_service = BookingService(db)
    return booking_service.get_job_bookings_for_employer(
        employer_id=current_employer.id,
        job_id=job_id,
        skip=skip,
        limit=limit,
    )
