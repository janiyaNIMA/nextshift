from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.job import JobResponse


class StudentPublicInfo(BaseModel):
    id: int
    name: str
    email: str

    model_config = ConfigDict(from_attributes=True)


class BookingResponse(BaseModel):
    id: int
    job_id: int
    student_id: int
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StudentBookingResponse(BaseModel):
    id: int
    job_id: int
    student_id: int
    status: str
    created_at: datetime
    job: JobResponse | None = None

    model_config = ConfigDict(from_attributes=True)


class EmployerBookingResponse(BaseModel):
    id: int
    job_id: int
    student_id: int
    status: str
    created_at: datetime
    student: StudentPublicInfo | None = None

    model_config = ConfigDict(from_attributes=True)
