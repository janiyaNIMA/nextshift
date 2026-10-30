from collections.abc import Generator
from typing import Annotated

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenException, UnauthorizedException
from app.core.security import decode_access_token
from app.db.session import SessionLocal
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository

security = HTTPBearer(auto_error=False)


def get_db() -> Generator[Session, None, None]:
    """Provides a transactional database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> User:
    """Validates the JWT access token and retrieves the current authenticated user."""
    if not credentials or not credentials.credentials:
        raise UnauthorizedException("Authentication credentials are required.")

    token = credentials.credentials
    try:
        payload = decode_access_token(token)
        user_id_str: str | None = payload.get("sub")
        if not user_id_str:
            raise UnauthorizedException("Invalid token subject.")
        user_id = int(user_id_str)
    except (jwt.PyJWTError, ValueError):
        raise UnauthorizedException("Could not validate authentication token.")

    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id)
    if not user:
        raise UnauthorizedException("Authenticated user no longer exists.")

    if not user.is_active:
        raise ForbiddenException("User account is inactive.")

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_role(*allowed_roles: UserRole):
    """Enforces role-based authorization for protected endpoints."""

    def role_checker(current_user: CurrentUser) -> User:
        if current_user.role not in allowed_roles:
            raise ForbiddenException("You do not have permission to perform this action.")
        return current_user

    return role_checker


RequireAdmin = Annotated[User, Depends(require_role(UserRole.ADMIN))]
RequireStudent = Annotated[User, Depends(require_role(UserRole.STUDENT))]
RequireEmployer = Annotated[User, Depends(require_role(UserRole.EMPLOYER))]


def require_approved_employer(
    current_user: Annotated[User, Depends(require_role(UserRole.EMPLOYER))],
) -> User:
    """Enforces that an employer's account has been approved by an administrator."""
    if not current_user.is_approved:
        raise ForbiddenException("Your employer account is pending administrator approval.")
    return current_user


RequireApprovedEmployer = Annotated[User, Depends(require_approved_employer)]
