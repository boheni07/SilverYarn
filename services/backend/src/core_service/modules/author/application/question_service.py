"""Question 유스케이스 — 현재는 GET /sync/download 조회 경로 하나뿐(질문 생성은
아직 이 세션 스코프 밖, question_repository.py 모듈 docstring 참조)."""

import uuid
from datetime import datetime

from core_service.modules.author.domain.question import Question
from core_service.modules.author.infrastructure.question_repository import QuestionRepository


class QuestionService:
    def __init__(self, repo: QuestionRepository):
        self._repo = repo

    async def list_priority_questions_for_user(
        self, user_id: uuid.UUID, since: datetime | None = None
    ) -> list[Question]:
        return await self._repo.list_unanswered_by_user(user_id, since)

    async def list_questions_for_user(
        self, user_id: uuid.UUID, answered: bool | None = None
    ) -> list[Question]:
        """GET /users/{userId}/questions (design.md §4.2, L-12) — 큐 전체 조회.
        sync/download의 priority_questions(미답변·`since` 이후만)와 달리 필터 없이 본다."""
        return await self._repo.list_by_user(user_id, answered)
