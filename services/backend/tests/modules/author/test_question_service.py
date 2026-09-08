"""QuestionService 유닛 테스트 — 페이크 Repository로 DB 없이 Application 계층 검증.

핵심 검증 대상: GET /sync/download의 priority_questions 소스 — 답변된 질문은
절대 섞이지 않는다, `since` 이후 새로 생긴 미답변 질문만 반환한다(question_repository.py
docstring의 created_at 근사 워터마크 설계).
"""

import uuid
from datetime import UTC, datetime, timedelta

from core_service.modules.author.application.question_service import QuestionService
from core_service.modules.author.domain.question import Question, QuestionType


class FakeQuestionRepository:
    def __init__(self) -> None:
        self.questions: list[Question] = []

    async def get_by_id(self, question_id: uuid.UUID) -> Question | None:
        return next((q for q in self.questions if q.id == question_id), None)

    async def list_unanswered_by_user(
        self, user_id: uuid.UUID, since: datetime | None = None
    ) -> list[Question]:
        result = [q for q in self.questions if q.user_id == user_id and not q.answered]
        if since is not None:
            result = [q for q in result if q.created_at > since]
        return sorted(result, key=lambda q: q.created_at)


def _make_question(
    user_id: uuid.UUID, text: str, answered: bool = False, created_at: datetime | None = None
) -> Question:
    return Question(
        id=uuid.uuid4(),
        user_id=user_id,
        linked_chapter_id=None,
        text=text,
        type=QuestionType.NEW_TOPIC,
        answered=answered,
        created_at=created_at or datetime.now(UTC),
    )


async def test_list_priority_questions_excludes_answered() -> None:
    repo = FakeQuestionRepository()
    service = QuestionService(repo)  # type: ignore[arg-type]
    user_id = uuid.uuid4()
    repo.questions.append(_make_question(user_id, "미답변 질문"))
    repo.questions.append(_make_question(user_id, "이미 답변한 질문", answered=True))

    result = await service.list_priority_questions_for_user(user_id)
    assert [q.text for q in result] == ["미답변 질문"]


async def test_list_priority_questions_since_excludes_older() -> None:
    repo = FakeQuestionRepository()
    service = QuestionService(repo)  # type: ignore[arg-type]
    user_id = uuid.uuid4()
    now = datetime.now(UTC)
    old = _make_question(user_id, "예전 질문", created_at=now - timedelta(days=1))
    new = _make_question(user_id, "새 질문", created_at=now)
    repo.questions.extend([old, new])

    result = await service.list_priority_questions_for_user(user_id, since=now - timedelta(hours=1))
    assert [q.id for q in result] == [new.id]


async def test_list_priority_questions_ignores_other_users() -> None:
    repo = FakeQuestionRepository()
    service = QuestionService(repo)  # type: ignore[arg-type]
    user_id = uuid.uuid4()
    other_user_id = uuid.uuid4()
    repo.questions.append(_make_question(other_user_id, "다른 사용자 질문"))

    result = await service.list_priority_questions_for_user(user_id)
    assert result == []
