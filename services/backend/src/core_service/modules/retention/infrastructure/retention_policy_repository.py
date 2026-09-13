"""retention_policies 테이블 SQLAlchemy 매핑 + Repository — schema.md §5 DDL과
1:1(마이그레이션 0012, decisions.md #56)."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Integer, String, select
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from core_service.core.db import Base
from core_service.modules.retention.domain.retention_policy import RetentionPolicy


class RetentionPolicyModel(Base):
    __tablename__ = "retention_policies"

    id: Mapped[uuid.UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    retention_days: Mapped[int] = mapped_column(Integer, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    def to_domain(self) -> RetentionPolicy:
        return RetentionPolicy(
            id=self.id, category=self.category, retention_days=self.retention_days, updated_at=self.updated_at
        )


class RetentionPolicyRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_category(self, category: str) -> RetentionPolicy | None:
        result = await self._session.execute(
            select(RetentionPolicyModel).where(RetentionPolicyModel.category == category)
        )
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def list_all(self) -> list[RetentionPolicy]:
        result = await self._session.execute(
            select(RetentionPolicyModel).order_by(RetentionPolicyModel.category)
        )
        return [m.to_domain() for m in result.scalars()]

    async def upsert(self, category: str, retention_days: int) -> RetentionPolicy:
        """마이그레이션이 심어둔 카테고리를 admin이 값만 바꾸는 게 일반 경로지만,
        새 카테고리를 SQL 없이 API로 먼저 만들어볼 수 있게 upsert로 둔다."""
        result = await self._session.execute(
            select(RetentionPolicyModel).where(RetentionPolicyModel.category == category)
        )
        model = result.scalar_one_or_none()
        now = datetime.now(UTC)
        if model is None:
            model = RetentionPolicyModel(
                id=uuid.uuid4(), category=category, retention_days=retention_days, updated_at=now
            )
            self._session.add(model)
        else:
            model.retention_days = retention_days
            model.updated_at = now
        await self._session.flush()
        return model.to_domain()
