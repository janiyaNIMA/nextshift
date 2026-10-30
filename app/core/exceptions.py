from typing import Any

from fastapi import status


class NextShiftException(Exception):
    """Base domain exception for NextShift.

    Demonstrates OOP Inheritance and Polymorphism: specialized exceptions
    override default HTTP status codes and provide custom error details.
    """

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_message: str = "An unexpected error occurred."

    def __init__(self, detail: str | None = None, data: Any | None = None) -> None:
        self.detail = detail or self.default_message
        self.data = data
        super().__init__(self.detail)


class NotFoundException(NextShiftException):
    """Raised when a requested resource is not found."""

    status_code: int = status.HTTP_404_NOT_FOUND
    default_message: str = "Resource not found."


class ConflictException(NextShiftException):
    """Raised on business logic conflicts, e.g. duplicate booking or email."""

    status_code: int = status.HTTP_409_CONFLICT
    default_message: str = "Resource conflict."


class ForbiddenException(NextShiftException):
    """Raised when an authenticated user lacks permission for the resource."""

    status_code: int = status.HTTP_403_FORBIDDEN
    default_message: str = "Operation not permitted."


class UnauthorizedException(NextShiftException):
    """Raised when authentication credentials are missing or invalid."""

    status_code: int = status.HTTP_401_UNAUTHORIZED
    default_message: str = "Could not validate credentials."


class BadRequestException(NextShiftException):
    """Raised when request arguments violate business rules."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    default_message: str = "Bad request."


class ValidationException(NextShiftException):
    """Raised for domain validation failures."""

    status_code: int = status.HTTP_422_UNPROCESSABLE_CONTENT
    default_message: str = "Validation failed."
