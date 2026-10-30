from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator


class JobCreate(BaseModel):
    title: Annotated[str, Field(min_length=3, max_length=255)]
    description: Annotated[str, Field(min_length=10)]
    category: Annotated[str, Field(min_length=2, max_length=100)]
    location: Annotated[str, Field(min_length=2, max_length=255)]
    pay_amount: Annotated[float, Field(ge=0.0, description="Nonnegative pay amount")]
    pay_unit: Annotated[str, Field(min_length=1, max_length=50, default="per_hour")]
    starts_at: datetime
    ends_at: datetime
    capacity: Annotated[int, Field(ge=1, default=1, description="Capacity must be at least 1")]

    @model_validator(mode="after")
    def validate_dates(self) -> "JobCreate":
        if self.ends_at <= self.starts_at:
            raise ValueError("ends_at must be strictly later than starts_at")
        return self


class JobResponse(BaseModel):
    id: int
    employer_id: int
    title: str
    description: str
    category: str
    location: str
    pay_amount: float
    pay_unit: str
    starts_at: datetime
    ends_at: datetime
    capacity: int
    remaining_capacity: int | None = None
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
