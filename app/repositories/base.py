from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Generic repository providing abstracted CRUD operations.

    Demonstrates Abstraction and Inheritance: encapsulates persistence mechanics
    and provides a consistent interface across different domain entities.
    """

    def __init__(self, model: type[ModelType], session: Session) -> None:
        self.model = model
        self.session = session

    def get_by_id(self, id: int) -> ModelType | None:
        return self.session.get(self.model, id)

    def list(self, skip: int = 0, limit: int = 100) -> list[ModelType]:
        stmt = select(self.model).offset(skip).limit(limit)
        return list(self.session.scalars(stmt).all())

    def create(self, instance: ModelType) -> ModelType:
        self.session.add(instance)
        self.session.flush()
        return instance

    def update(self, instance: ModelType) -> ModelType:
        self.session.add(instance)
        self.session.flush()
        return instance

    def delete(self, instance: ModelType) -> None:
        self.session.delete(instance)
        self.session.flush()

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()
