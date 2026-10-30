from fastapi import APIRouter, Query

from app.api.deps import DbSession, RequireAdmin
from app.schemas.job import JobResponse
from app.schemas.user import UserResponse
from app.services.admin_service import AdminService

router = APIRouter(prefix="/admin", tags=["Admin Operations"])


@router.get(
    "/employers/pending",
    response_model=list[UserResponse],
    summary="List pending employer registration approvals (Admin only)",
)
def list_pending_employers(
    _: RequireAdmin,
    db: DbSession,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    admin_service = AdminService(db)
    return admin_service.list_pending_employers(skip=skip, limit=limit)


@router.patch(
    "/employers/{user_id}/approve",
    response_model=UserResponse,
    summary="Approve pending employer account (Admin only)",
)
def approve_employer(
    user_id: int,
    _: RequireAdmin,
    db: DbSession,
):
    admin_service = AdminService(db)
    return admin_service.approve_employer(user_id=user_id)


@router.get(
    "/jobs/pending",
    response_model=list[JobResponse],
    summary="List pending vacancy postings awaiting moderation (Admin only)",
)
def list_pending_jobs(
    _: RequireAdmin,
    db: DbSession,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    admin_service = AdminService(db)
    return admin_service.list_pending_jobs(skip=skip, limit=limit)


@router.patch(
    "/jobs/{job_id}/approve",
    response_model=JobResponse,
    summary="Approve and publish a pending vacancy (Admin only)",
)
def approve_job(
    job_id: int,
    _: RequireAdmin,
    db: DbSession,
):
    admin_service = AdminService(db)
    return admin_service.approve_job(job_id=job_id)
