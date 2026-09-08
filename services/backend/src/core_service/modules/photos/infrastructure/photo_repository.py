"""photos 테이블 SQLAlchemy 매핑 + Repository — schema.md §3.6/§5 DDL과 1:1.

`linked_chunk_id`는 DB에는 `conversation_chunks(id)` FK 제약이 있지만(erd.md §1
의도적 비정규화 2, 양방향 FK) ORM에는 FK로 선언하지 않았다 — 두 테이블을 서로
`ForeignKey`로 선언하면 SQLAlchemy가 순환 의존으로 취급해야 하는데, 이 프로젝트는
ORM `relationship()`을 쓰지 않고 Repository로만 조회하므로 얻는 실익이 없다.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, SmallInteger, String, select
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from core_service.core.db import Base
from core_service.modules.photos.domain.photo import (
    Photo,
    PhotoUploadStatus,
    PlacementStatus,
    QualityFlag,
    RecallStatus,
    UploaderType,
)


class PhotoModel(Base):
    __tablename__ = "photos"

    id: Mapped[uuid.UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    uploader_type: Mapped[str] = mapped_column(
        SAEnum("family", "self", name="uploader_type", create_type=False), nullable=False
    )
    status: Mapped[str] = mapped_column(
        SAEnum("pending_upload", "uploaded", name="photo_upload_status", create_type=False),
        nullable=False,
        default="pending_upload",
    )
    storage_ref: Mapped[str] = mapped_column(String(500), nullable=False)
    caption: Mapped[str | None] = mapped_column(String(300), nullable=True)
    year_tag: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    recall_status: Mapped[str] = mapped_column(
        SAEnum("pending", "completed", name="recall_status", create_type=False),
        nullable=False,
        default="pending",
    )
    placement_status: Mapped[str] = mapped_column(
        SAEnum("proposed", "confirmed", name="placement_status", create_type=False),
        nullable=False,
        default="proposed",
    )
    inline_position: Mapped[str | None] = mapped_column(String(50), nullable=True)
    linked_chunk_id: Mapped[uuid.UUID | None] = mapped_column(
        PgUUID(as_uuid=True), nullable=True
    )  # FK 미선언 사유는 모듈 docstring 참조
    linked_chapter_id: Mapped[uuid.UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("chapters.id"), nullable=True
    )
    quality_flag: Mapped[str] = mapped_column(
        SAEnum("ok", "blurry", "inappropriate", "unreviewed", name="quality_flag", create_type=False),
        nullable=False,
        default="unreviewed",
    )
    width: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    height: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    file_size_kb: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    def to_domain(self) -> Photo:
        return Photo(
            id=self.id,
            user_id=self.user_id,
            uploader_type=UploaderType(self.uploader_type),
            status=PhotoUploadStatus(self.status),
            storage_ref=self.storage_ref,
            caption=self.caption,
            year_tag=self.year_tag,
            recall_status=RecallStatus(self.recall_status),
            placement_status=PlacementStatus(self.placement_status),
            inline_position=self.inline_position,
            linked_chunk_id=self.linked_chunk_id,
            linked_chapter_id=self.linked_chapter_id,
            quality_flag=QualityFlag(self.quality_flag),
            width=self.width,
            height=self.height,
            file_size_kb=self.file_size_kb,
            mime_type=self.mime_type,
            uploaded_at=self.uploaded_at,
        )


class PhotoRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, photo_id: uuid.UUID) -> Photo | None:
        model = await self._session.get(PhotoModel, photo_id)
        return model.to_domain() if model else None

    async def list_by_user(self, user_id: uuid.UUID) -> list[Photo]:
        """design.md §4.2 `GET /users/{userId}/photos` — 최신 업로드 우선.
        idx_photos_user_recall(user_id, recall_status)이 이 조회의 user_id
        prefix는 타지만 정렬 컬럼(uploaded_at)까지는 커버 안 함 — photos 규모가
        sync_sessions만큼 안 커질 걸로 보고 지금은 감수(schema.md §6)."""
        stmt = select(PhotoModel).where(PhotoModel.user_id == user_id).order_by(PhotoModel.uploaded_at.desc())
        result = await self._session.execute(stmt)
        return [model.to_domain() for model in result.scalars()]

    async def create_pending(
        self,
        photo_id: uuid.UUID,
        user_id: uuid.UUID,
        uploader_type: UploaderType,
        storage_ref: str,
        mime_type: str | None,
        file_size_kb: int | None,
    ) -> Photo:
        """sync-contract.md §4 1단계 — Presigned URL 발급과 동시에 status=pending_upload로
        행을 만든다(3단계 확인 콜백이 안 오면 이 행이 orphan cleanup 대상이 된다 —
        배치 잡 자체는 아직 미구현, photos/__init__.py 참조)."""
        model = PhotoModel(
            id=photo_id,
            user_id=user_id,
            uploader_type=uploader_type.value,
            status=PhotoUploadStatus.PENDING_UPLOAD.value,
            storage_ref=storage_ref,
            mime_type=mime_type,
            file_size_kb=file_size_kb,
            uploaded_at=datetime.now(UTC),
        )
        self._session.add(model)
        await self._session.flush()
        return model.to_domain()

    async def mark_uploaded(self, photo_id: uuid.UUID) -> Photo:
        """sync-contract.md §4 3단계 — `POST /photos/{id}/complete` 확인 콜백."""
        model = await self._session.get(PhotoModel, photo_id)
        if model is None:
            raise LookupError(f"photo {photo_id} not found")
        model.status = PhotoUploadStatus.UPLOADED.value
        await self._session.flush()
        return model.to_domain()

    async def list_pending_upload_older_than(self, threshold: datetime) -> list[Photo]:
        """orphan cleanup 배치(sync-contract.md §4)의 대상 조회 — 3단계 확인 콜백이
        `threshold` 이전에 생성된 행 중 아직도 안 온 것들. `uploaded_at`은 생성
        시각으로 즉시 세팅되므로(create_pending) "얼마나 오래 pending_upload로
        남아 있었는지"의 근사값으로 쓸 수 있다."""
        stmt = select(PhotoModel).where(
            PhotoModel.status == PhotoUploadStatus.PENDING_UPLOAD.value,
            PhotoModel.uploaded_at < threshold,
        )
        result = await self._session.execute(stmt)
        return [model.to_domain() for model in result.scalars()]

    async def delete(self, photo_id: uuid.UUID) -> None:
        """orphan cleanup 배치 전용 — 실제 업로드가 끝내 확인되지 않은 행은 복구할
        내용이 없어(사진 자체가 없거나 있어도 메타데이터 미완성) 그냥 지운다."""
        model = await self._session.get(PhotoModel, photo_id)
        if model is not None:
            await self._session.delete(model)
            await self._session.flush()
