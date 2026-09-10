"""QuestionService 유닛 테스트 — 페이크 Repository로 DB 없이 Application 계층 검증.

핵심 검증 대상: GET /sync/download의 priority_questions 소스 — 답변된 질문은
절대 섞이지 않는다, `since` 이후 새로 생긴 미답변 질문만 반환한다(question_repository.py
docstring의 created_at 근사 워터마크 설계).
"""

import uuid
from datetime import UTC, datetime, timedelta

from core_service.modules.author.application.question_service import QuestionService
from core_service.modules.author.domain.question import GeneratedQuestion, Question, QuestionType


class FakeQuestionRepository:
    def __init__(self) -> None:
        self.questions: list[Question] = []

    async def get_by_id(self, question_id: uuid.UUID) -> Question | None:
        return next((q for q in self.questions if q.id == question_id), None)

    async def count_unanswered_by_user(self, user_id: uuid.UUID) -> int:
        return sum(1 for q in self.questions if q.user_id == user_id and not q.answered)

    async def create_many(
        self,
        user_id: uuid.UUID,
        linked_chapter_id: uuid.UUID | None,
        items: list[GeneratedQuestion],
    ) -> list[Question]:
        created = [
            Question(
                id=uuid.uuid4(),
                user_id=user_id,
                linked_chapter_id=linked_chapter_id,
                text=it.text,
                type=it.type,
                answered=False,
                created_at=datetime.now(UTC),
            )
            for it in items
        ]
        self.questions.extend(created)
        return created

    async def list_unanswered_by_user(
        self, user_id: uuid.UUID, since: datetime | None = None
    ) -> list[Question]:
        result = [q for q in self.questions if q.user_id == user_id and not q.answered]
        if since is not None:
            result = [q for q in result if q.created_at > since]
        return sorted(result, key=lambda q: q.created_at)

    async def list_by_user(self, user_id: uuid.UUID, answered: bool | None = None) -> list[Question]:
        result = [q for q in self.questions if q.user_id == user_id]
        if answered is not None:
            result = [q for q in result if q.answered == answered]
        return sorted(result, key=lambda q: (q.answered, q.created_at))


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


async def test_list_questions_for_user_returns_all_unanswered_first() -> None:
    """GET /users/{userId}/questions — priority와 달리 답변된 것도 포함, 미답변 우선 정렬."""
    repo = FakeQuestionRepository()
    service = QuestionService(repo)  # type: ignore[arg-type]
    user_id = uuid.uuid4()
    now = datetime.now(UTC)
    repo.questions.append(
        _make_question(user_id, "답변됨", answered=True, created_at=now - timedelta(days=2))
    )
    repo.questions.append(_make_question(user_id, "미답변2", created_at=now))
    repo.questions.append(_make_question(user_id, "미답변1", created_at=now - timedelta(days=1)))

    result = await service.list_questions_for_user(user_id)
    assert [q.text for q in result] == ["미답변1", "미답변2", "답변됨"]


async def test_list_questions_for_user_answered_filter() -> None:
    repo = FakeQuestionRepository()
    service = QuestionService(repo)  # type: ignore[arg-type]
    user_id = uuid.uuid4()
    repo.questions.append(_make_question(user_id, "답변됨", answered=True))
    repo.questions.append(_make_question(user_id, "미답변"))

    assert [q.text for q in await service.list_questions_for_user(user_id, answered=False)] == ["미답변"]
    assert [q.text for q in await service.list_questions_for_user(user_id, answered=True)] == ["답변됨"]


# --- Critic Agent (generate_followups) ---


class _FakeCritic:
    def __init__(self, out: list[tuple[str, str]]) -> None:
        self._out = out
        self.calls = 0
        self.last_existing: list[str] = []

    async def critique_and_generate_questions(
        self, chapter_body: str, latest_transcript: str, existing_question_texts: list[str]
    ) -> list[tuple[str, str]]:
        self.calls += 1
        self.last_existing = existing_question_texts
        return self._out


async def test_generate_followups_inserts_up_to_three_typed_questions() -> None:
    repo = FakeQuestionRepository()
    service = QuestionService(repo)  # type: ignore[arg-type]
    user_id, chapter_id = uuid.uuid4(), uuid.uuid4()
    critic = _FakeCritic(
        [
            ("첫 월급으로 무엇을 하셨어요?", "follow_up"),
            ("그 시절 친구분들 이야기를 들려주세요.", "new_topic"),
            ("공장 일은 힘들지 않으셨나요?", "follow_up"),
            ("네 번째 질문(버려짐)", "follow_up"),
        ]
    )

    created = await service.generate_followups(user_id, chapter_id, "본문", "구술", critic)

    assert len(created) == 3
    assert all(q.linked_chapter_id == chapter_id and not q.answered for q in created)
    assert {q.type for q in created} == {QuestionType.FOLLOW_UP, QuestionType.NEW_TOPIC}


async def test_generate_followups_skips_duplicates_and_bad_types() -> None:
    repo = FakeQuestionRepository()
    service = QuestionService(repo)  # type: ignore[arg-type]
    user_id = uuid.uuid4()
    repo.questions.append(_make_question(user_id, "이미 있는 질문입니다"))
    critic = _FakeCritic(
        [
            ("  이미 있는 질문입니다 ", "follow_up"),  # 공백만 다름 → 중복
            ("유효한 새 질문", "unknown_type"),  # 알 수 없는 type → 버림
            ("진짜 새 질문", "new_topic"),
        ]
    )

    created = await service.generate_followups(user_id, uuid.uuid4(), "본문", "구술", critic)

    assert [q.text for q in created] == ["진짜 새 질문"]
    assert "이미 있는 질문입니다" in critic.last_existing  # 컨텍스트로 넘겨줌


async def test_generate_followups_skips_when_queue_full() -> None:
    repo = FakeQuestionRepository()
    service = QuestionService(repo)  # type: ignore[arg-type]
    user_id = uuid.uuid4()
    for i in range(8):
        repo.questions.append(_make_question(user_id, f"대기 질문 {i}"))
    critic = _FakeCritic([("새 질문", "new_topic")])

    created = await service.generate_followups(user_id, uuid.uuid4(), "본문", "구술", critic)

    assert created == []
    assert critic.calls == 0  # 큐가 꽉 찼으면 LLM 호출조차 안 함
