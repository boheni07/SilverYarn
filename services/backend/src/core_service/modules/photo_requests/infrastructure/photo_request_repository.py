"""photo_requests 테이블 SQLAlchemy 매핑 + Repository — schema.md §3.7/§5 DDL과 1:1."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String, select
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from core_service.core.db import Base
from core_service.modules.photo_requests.domain.photo_request import PhotoRequest, PhotoRequestStatus


class PhotoRequestModel(Base):
    __tablename__ = "photo_requests"

    id: Mapped[uuid.UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    requested_by: Mapped[uuid.UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("family_members.id"), nullable=True
    )
    message: Mapped[str | None] = mapped_column(String(300), nullable=True)
    status: Mapped[str] = mapped_column(
        SAEnum("pending", "fulfilled", "dismissed", name="photo_request_status", create_type=False),
        nullable=False,
        default="pending",
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    fulfilled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def to_domain(self) -> PhotoRequest:
        return PhotoRequest(
            id=self.id,
            user_id=self.user_id,
            requested_by=self.requested_by,
            message=self.message,
            status=PhotoRequestStatus(self.status),
            created_at=self.created_at,
            fulfilled_at=self.fulfilled_at,
        )


class PhotoRequestRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, request_id: uuid.UUID) -> PhotoRequest | None:
        model = await self._session.get(PhotoRequestModel, request_id)
        return model.to_domain() if model else None

    async def list_by_user(self, user_id: uuid.UUID) -> list[PhotoRequest]:
        result = await self._session.execute(
            select(PhotoRequestModel)
            .where(PhotoRequestModel.user_id == user_id)
            .order_by(PhotoRequestModel.created_at.desc())
        )
        return [m.to_domain() for m in result.scalars()]

    async def list_pending_by_user(self, user_id: uuid.UUID) -> list[PhotoRequest]:
        """photos 모듈이 업로드 완료 시 자동 충족 처리할 대상을 찾는 용도
        (photo_service.py의 fulfill 호출 경로 참조)."""
        result = await self._session.execute(
            select(PhotoRequestModel).where(
                PhotoRequestModel.user_id == user_id,
                PhotoRequestModel.status == PhotoRequestStatus.PENDING.value,
            )
        )
        return [m.to_domain() for m in result.scalars()]

    async def create(
        self, user_id: uuid.UUID, requested_by: uuid.UUID | None, message: str | None
    ) -> PhotoRequest:
        model = PhotoRequestModel(
            id=uuid.uuid4(),
            user_id=user_id,
            requested_by=requested_by,
            message=message,
            status=PhotoRequestStatus.PENDING.value,
            created_at=datetime.now(UTC),
            fulfilled_at=None,
        )
        self._session.add(model)
        await self._session.flush()
        return model.to_domain()

    async def update_status(
        self, request_id: uuid.UUID, status: PhotoRequestStatus, fulfilled_at: datetime | None = None
    ) -> PhotoRequest:
        model = await self._session.get(PhotoRequestModel, request_id)
        if model is None:
            raise LookupError(f"photo_request {request_id} not found")
        model.status = status.value
        if fulfilled_at is not None:
            model.fulfilled_at = fulfilled_at
        await self._session.flush()
        return model.to_domain()
