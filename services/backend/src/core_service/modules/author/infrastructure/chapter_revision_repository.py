"""chapter_revisions 테이블 SQLAlchemy 매핑 + Repository — schema.md §5 DDL과 1:1.

감수 시점에만 생성된다(3차 검증 M-5) — 이 Repository의 유일한 쓰기 경로는
ChapterService.review_chapter()를 거치는 것이며, 작가 엔진 초안 생성 단계(§4)에서는
호출되지 않는다.

`body_text_snapshot`은 PII 암호화 대상(schema.md §5, decisions.md #45) — 챕터 소유자의
DEK로 암호화한다(core/crypto.py). 소유자 user_id는 create()에서 명시적으로 받고,
조회에서는 chapters 조인으로 얻는다.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text, select
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from core_service.core.crypto import PiiFieldEncryptor, get_pii_encryptor
from core_service.core.db import Base
from core_service.modules.author.domain.chapter import ChapterRevision, RevisionAction
from core_service.modules.author.infrastructure.chapter_repository import ChapterModel


class ChapterRevisionModel(Base):
    __tablename__ = "chapter_revisions"

    id: Mapped[uuid.UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True)
    chapter_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("chapters.id", ondelete="CASCADE"), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    body_text_snapshot: Mapped[str] = mapped_column(Text, nullable=False)  # 저장 시 암호문
    reviewer_id: Mapped[uuid.UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("family_members.id"), nullable=True
    )
    review_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    action: Mapped[str] = mapped_column(
        SAEnum("approved", "rejected", name="revision_action", create_type=False), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ChapterRevisionRepository:
    def __init__(self, session: AsyncSession, pii: PiiFieldEncryptor | None = None):
        self._session = session
        self._pii = pii or get_pii_encryptor()

    async def _to_domain(self, model: ChapterRevisionModel, owner_id: uuid.UUID) -> ChapterRevision:
        return ChapterRevision(
            id=model.id,
            chapter_id=model.chapter_id,
            version=model.version,
            body_text_snapshot=await self._pii.decrypt(self._session, owner_id, model.body_text_snapshot),
            reviewer_id=model.reviewer_id,
            review_comment=model.review_comment,
            action=RevisionAction(model.action),
            created_at=model.created_at,
        )

    async def list_by_chapter(self, chapter_id: uuid.UUID) -> list[ChapterRevision]:
        result = await self._session.execute(
            select(ChapterRevisionModel, ChapterModel.user_id)
            .join(ChapterModel, ChapterModel.id == ChapterRevisionModel.chapter_id)
            .where(ChapterRevisionModel.chapter_id == chapter_id)
            .order_by(ChapterRevisionModel.created_at.desc())
        )
        return [await self._to_domain(model, owner_id) for model, owner_id in result.all()]

    async def create(
        self,
        chapter_id: uuid.UUID,
        user_id: uuid.UUID,
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
            body_text_snapshot=await self._pii.encrypt(self._session, user_id, body_text_snapshot),
            reviewer_id=reviewer_id,
            review_comment=review_comment,
            action=action.value,
            created_at=datetime.now(UTC),
        )
        self._session.add(model)
        await self._session.flush()
        return await self._to_domain(model, user_id)
