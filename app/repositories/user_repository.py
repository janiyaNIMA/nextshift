from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, session: Session) -> None:
        super().__init__(User, session)

    def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        return self.session.scalars(stmt).first()

    def list_pending_employers(self, skip: int = 0, limit: int = 50) -> list[User]:
        stmt = (
            select(User)
            .where(User.role == UserRole.EMPLOYER, User.is_approved.is_(False))
            .order_by(User.created_at.asc())
            .offset(skip)
            .limit(limit)
        )
        return list(self.session.scalars(stmt).all())
