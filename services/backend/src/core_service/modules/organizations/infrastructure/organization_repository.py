"""organizations 테이블 SQLAlchemy 매핑 + Repository — schema.md §5 DDL과 1:1
(마이그레이션 0011, decisions.md #59)."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, String, func, select
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from core_service.core.db import Base
from core_service.modules.organizations.domain.organization import Organization


class OrganizationModel(Base):
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    def to_domain(self) -> Organization:
        return Organization(id=self.id, name=self.name, created_at=self.created_at)


class OrganizationRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, org_id: uuid.UUID) -> Organization | None:
        model = await self._session.get(OrganizationModel, org_id)
        return model.to_domain() if model else None

    async def list_all(self) -> list[Organization]:
        result = await self._session.execute(
            select(OrganizationModel).order_by(OrganizationModel.created_at.desc())
        )
        return [m.to_domain() for m in result.scalars()]

    async def create(self, name: str) -> Organization:
        model = OrganizationModel(
            id=uuid.uuid4(),
            name=name,
            created_at=datetime.now(UTC),
        )
        self._session.add(model)
        await self._session.flush()
        return model.to_domain()

    async def exists(self, org_id: uuid.UUID) -> bool:
        result = await self._session.execute(
            select(func.count()).select_from(OrganizationModel).where(OrganizationModel.id == org_id)
        )
        return result.scalar_one() > 0
