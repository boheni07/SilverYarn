"""publications 테이블 SQLAlchemy 매핑 + Repository — schema.md §3.17 DDL과 1:1."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, String, select
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from core_service.core.db import Base
from core_service.modules.publications.domain.publication import (
    Publication,
    PublicationFormat,
    PublicationStatus,
)


class PublicationModel(Base):
    __tablename__ = "publications"

    id: Mapped[uuid.UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    format: Mapped[str] = mapped_column(
        SAEnum("hardcover_pdf", "epub", name="publication_format", create_type=False), nullable=False
    )
    status: Mapped[str] = mapped_column(
        SAEnum("requested", "processing", "ready", "delivered", name="publication_status", create_type=False),
        nullable=False,
    )
    storage_ref: Mapped[str | None] = mapped_column(String(500), nullable=True)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class PublicationRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    def _to_domain(self, model: PublicationModel) -> Publication:
        return Publication(
            id=model.id,
            user_id=model.user_id,
            format=PublicationFormat(model.format),
            status=PublicationStatus(model.status),
            storage_ref=model.storage_ref,
            requested_at=model.requested_at,
            completed_at=model.completed_at,
        )

    async def get_by_id(self, publication_id: uuid.UUID) -> Publication | None:
        model = await self._session.get(PublicationModel, publication_id)
        return self._to_domain(model) if model else None

    async def list_by_user(self, user_id: uuid.UUID) -> list[Publication]:
        result = await self._session.execute(
            select(PublicationModel)
            .where(PublicationModel.user_id == user_id)
            .order_by(PublicationModel.requested_at.desc())
        )
        return [self._to_domain(m) for m in result.scalars().all()]

    async def create(self, user_id: uuid.UUID, fmt: PublicationFormat) -> Publication:
        model = PublicationModel(
            id=uuid.uuid4(),
            user_id=user_id,
            format=fmt.value,
            status=PublicationStatus.REQUESTED.value,
            storage_ref=None,
            requested_at=datetime.now(UTC),
            completed_at=None,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_domain(model)

    async def mark_processing(self, publication_id: uuid.UUID) -> None:
        model = await self._session.get(PublicationModel, publication_id)
        if model is None:
            raise LookupError(f"publication {publication_id} not found")
        model.status = PublicationStatus.PROCESSING.value
        await self._session.flush()

    async def mark_ready(self, publication_id: uuid.UUID, storage_ref: str) -> None:
        model = await self._session.get(PublicationModel, publication_id)
        if model is None:
            raise LookupError(f"publication {publication_id} not found")
        model.status = PublicationStatus.READY.value
        model.storage_ref = storage_ref
        model.completed_at = datetime.now(UTC)
        await self._session.flush()
