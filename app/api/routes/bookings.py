from fastapi import APIRouter, Query

from app.api.deps import DbSession, RequireStudent
from app.schemas.booking import StudentBookingResponse
from app.services.booking_service import BookingService

router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.get(
    "/me",
    response_model=list[StudentBookingResponse],
    summary="View student's own bookings",
)
def get_my_bookings(
    current_student: RequireStudent,
    db: DbSession,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    booking_service = BookingService(db)
    return booking_service.get_student_bookings(
        student_id=current_student.id,
        skip=skip,
        limit=limit,
    )
