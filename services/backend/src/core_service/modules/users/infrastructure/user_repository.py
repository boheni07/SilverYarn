"""users 테이블 SQLAlchemy 매핑 + Repository — schema.md §5 DDL과 1:1."""

import uuid
from datetime import UTC, date, datetime

from sqlalchemy import Date, DateTime, String
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from core_service.core.db import Base
from core_service.modules.users.domain.user import User


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    primary_device_id: Mapped[uuid.UUID | None] = mapped_column(PgUUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    def to_domain(self) -> User:
        return User(
            id=self.id,
            name=self.name,
            birth_date=self.birth_date,
            primary_device_id=self.primary_device_id,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )


class UserRepository:
    """Domain이 필요로 하는 영속화 인터페이스의 구현체 (structure.md §6 의존성 역전)."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        model = await self._session.get(UserModel, user_id)
        return model.to_domain() if model else None

    async def create(self, name: str, birth_date: date | None) -> User:
        model = UserModel(
            id=uuid.uuid4(),
            name=name,
            birth_date=birth_date,
            primary_device_id=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        self._session.add(model)
        await self._session.flush()
        return model.to_domain()

    async def set_primary_device(self, user_id: uuid.UUID, device_id: uuid.UUID) -> None:
        model = await self._session.get(UserModel, user_id)
        if model is None:
            raise LookupError(f"user {user_id} not found")
        model.primary_device_id = device_id
        model.updated_at = datetime.now(UTC)
        await self._session.flush()
