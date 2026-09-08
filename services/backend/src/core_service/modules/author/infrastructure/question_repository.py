"""questions 테이블 SQLAlchemy 매핑 + Repository — schema.md §3.9 DDL과 1:1."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Text, select
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from core_service.core.db import Base
from core_service.modules.author.domain.question import Question, QuestionType


class QuestionModel(Base):
    __tablename__ = "questions"

    id: Mapped[uuid.UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    linked_chapter_id: Mapped[uuid.UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("chapters.id"), nullable=True
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(
        SAEnum("new_topic", "follow_up", name="question_type", create_type=False),
        nullable=False,
    )
    answered: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    def to_domain(self) -> Question:
        return Question(
            id=self.id,
            user_id=self.user_id,
            linked_chapter_id=self.linked_chapter_id,
            text=self.text,
            type=QuestionType(self.type),
            answered=self.answered,
            created_at=self.created_at,
        )


class QuestionRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, question_id: uuid.UUID) -> Question | None:
        model = await self._session.get(QuestionModel, question_id)
        return model.to_domain() if model else None

    async def list_unanswered_by_user(
        self, user_id: uuid.UUID, since: datetime | None = None
    ) -> list[Question]:
        """GET /sync/download의 priority_questions 소스.

        questions에는 갱신 워터마크(updated_at)가 없다(schema.md §3.9 — 답변
        여부만 바뀌는 단순 큐라 별도 두지 않았다) — 그래서 sync-contract.md §5의
        "updated_at 기준 워터마크" 원칙을 그대로 못 쓰고, 대신 `created_at`을
        근사 워터마크로 쓴다: `since` 이후 새로 생긴 미답변 질문만 돌려준다.
        미답변 상태가 그대로인 오래된 질문은 이미 한 번 내려받아 로컬 캐시에
        있다고 가정 — 재전송하지 않는다(진짜 갱신 로그가 필요해지면 `answered`
        전환 시각을 남길 컬럼 추가 검토).
        """
        conditions = [QuestionModel.user_id == user_id, QuestionModel.answered.is_(False)]
        if since is not None:
            conditions.append(QuestionModel.created_at > since)
        result = await self._session.execute(
            select(QuestionModel).where(*conditions).order_by(QuestionModel.created_at)
        )
        return [m.to_domain() for m in result.scalars().all()]
