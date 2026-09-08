"""photos 테이블 SQLAlchemy 매핑 — schema.md §5 DDL과 1:1.

⚠️ Repository 클래스는 아직 없다(photos/__init__.py 참조) — 지금은 ORM 모델을
`Base.metadata`에 등록해 다른 모듈(`care.conversation_chunks.linked_photo_id`)의
FK 해석을 가능하게 하는 것이 유일한 목적이다.

`linked_chunk_id`는 DB에는 `conversation_chunks(id)` FK 제약이 있지만(erd.md §1
의도적 비정규화 2, 양방향 FK) ORM에는 FK로 선언하지 않았다 — 두 테이블을 서로
`ForeignKey`로 선언하면 SQLAlchemy가 순환 의존으로 취급해야 하는데, 이 프로젝트는
ORM `relationship()`을 쓰지 않고 Repository로만 조회하므로 얻는 실익이 없다.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, SmallInteger, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from core_service.core.db import Base


class PhotoModel(Base):
    __tablename__ = "photos"

    id: Mapped[uuid.UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    uploader_type: Mapped[str] = mapped_column(
        SAEnum("family", "self", name="uploader_type", create_type=False), nullable=False
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
