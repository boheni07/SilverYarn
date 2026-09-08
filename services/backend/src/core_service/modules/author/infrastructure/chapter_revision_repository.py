"""chapter_revisions 테이블 SQLAlchemy 매핑 + Repository — schema.md §5 DDL과 1:1.

감수 시점에만 생성된다(3차 검증 M-5) — 이 Repository의 유일한 쓰기 경로는
ChapterService.review_chapter()를 거치는 것이며, 작가 엔진 초안 생성 단계(§4)에서는
호출되지 않는다.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text, select
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from core_service.core.db import Base
from core_service.modules.author.domain.chapter import ChapterRevision, RevisionAction


class ChapterRevisionModel(Base):
    __tablename__ = "chapter_revisions"

    id: Mapped[uuid.UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True)
    chapter_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("chapters.id", ondelete="CASCADE"), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    body_text_snapshot: Mapped[str] = mapped_column(Text, nullable=False)
    reviewer_id: Mapped[uuid.UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("family_members.id"), nullable=True
    )
    review_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    action: Mapped[str] = mapped_column(
        SAEnum("approved", "rejected", name="revision_action", create_type=False), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    def to_domain(self) -> ChapterRevision:
        return ChapterRevision(
            id=self.id,
            chapter_id=self.chapter_id,
            version=self.version,
            body_text_snapshot=self.body_text_snapshot,
            reviewer_id=self.reviewer_id,
            review_comment=self.review_comment,
            action=RevisionAction(self.action),
            created_at=self.created_at,
        )


class ChapterRevisionRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def list_by_chapter(self, chapter_id: uuid.UUID) -> list[ChapterRevision]:
        result = await self._session.execute(
            select(ChapterRevisionModel)
            .where(ChapterRevisionModel.chapter_id == chapter_id)
            .order_by(ChapterRevisionModel.created_at.desc())
        )
        return [m.to_domain() for m in result.scalars().all()]

    async def create(
        self,
        chapter_id: uuid.UUID,
        version: int,
        body_text_snapshot: str,
        reviewer_id: uuid.UUID | None,
        review_comment: str | None,
        action: RevisionAction,
    ) -> ChapterRevision:
        model = ChapterRevisionModel(
            id=uuid.uuid4(),
            chapter_id=chapter_id,
            version=version,
            body_text_snapshot=body_text_snapshot,
            reviewer_id=reviewer_id,
            review_comment=review_comment,
            action=action.value,
            created_at=datetime.now(UTC),
        )
        self._session.add(model)
        await self._session.flush()
        return model.to_domain()
