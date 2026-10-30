from sqlalchemy.orm import Session

from app.core.exceptions import (
    ConflictException,
    ForbiddenException,
    UnauthorizedException,
)
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.auth import Token
from app.schemas.user import PublicRegisterRole, UserRegisterRequest


class AuthService:
    """Service encapsulating user authentication and registration logic."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.user_repo = UserRepository(session)

    def register(self, user_in: UserRegisterRequest) -> User:
        existing = self.user_repo.get_by_email(user_in.email)
        if existing:
            raise ConflictException("A user with this email already exists.")

        # Assign role & approval status based on business rules
        if user_in.role == PublicRegisterRole.STUDENT:
            role = UserRole.STUDENT
            is_approved = True  # Students are active immediately
        elif user_in.role == PublicRegisterRole.EMPLOYER:
            role = UserRole.EMPLOYER
            is_approved = False  # Employers require admin approval before posting jobs
        else:
            raise ConflictException("Invalid role for public registration.")

        new_user = User(
            name=user_in.name.strip(),
            email=user_in.email.lower().strip(),
            password_hash=get_password_hash(user_in.password),
            role=role,
            is_active=True,
            is_approved=is_approved,
        )
        self.user_repo.create(new_user)
        self.session.commit()
        self.session.refresh(new_user)
        return new_user

    def authenticate(self, email: str, password: str) -> User:
        user = self.user_repo.get_by_email(email.lower().strip())
        if not user or not verify_password(password, user.password_hash):
            raise UnauthorizedException("Incorrect email or password.")

        if not user.is_active:
            raise ForbiddenException("User account is inactive. Please contact support.")

        return user

    def create_token_for_user(self, user: User) -> Token:
        token = create_access_token(
            subject=user.id,
            extra_claims={
                "role": user.role.value,
                "email": user.email,
            },
        )
        return Token(access_token=token, token_type="bearer")
