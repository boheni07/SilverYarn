"""Question 유스케이스 — 조회(GET /sync/download, GET /users/{id}/questions)와
Critic Agent 질문 생성(design.md §2.11 3단계, workflow-diagrams.md §4).
"""

import uuid
from datetime import datetime
from typing import Protocol

from core_service.modules.author.domain.question import (
    GeneratedQuestion,
    Question,
    QuestionType,
)
from core_service.modules.author.infrastructure.question_repository import QuestionRepository

# 미답변 질문이 이 수 이상 쌓여 있으면 Critic Agent를 돌리지 않는다 — 큐가 넘쳐
# 어르신이 압도되지 않도록(기획서 4장 "한 번에 하나씩"). 답변이 소진되면 다시 생성.
_MAX_OPEN_QUESTIONS = 8
# 한 번 실행에서 새로 넣을 질문 상한 (design.md §2.11 "Top-3").
_MAX_NEW_PER_RUN = 3


class QuestionCritic(Protocol):
    """design §2.11 3단계 — 챕터 본문·최근 구술 → 회고 질문 초안 `[(text, type_str), ...]`.
    `core.clients.LLMClient`가 구현."""

    async def critique_and_generate_questions(
        self,
        chapter_body: str,
        latest_transcript: str,
        existing_question_texts: list[str],
    ) -> list[tuple[str, str]]: ...


def _normalize(text: str) -> str:
    return " ".join(text.split()).casefold()


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

    async def generate_followups(
        self,
        user_id: uuid.UUID,
        linked_chapter_id: uuid.UUID | None,
        chapter_body: str,
        latest_transcript: str,
        critic: QuestionCritic,
    ) -> list[Question]:
        """design §2.11 3단계 Critic Agent — 챕터 갱신 후 심층 질문 Top-3을 큐에 넣는다.

        - 미답변 큐가 이미 `_MAX_OPEN_QUESTIONS` 이상이면 생성하지 않는다(큐 범람 방지).
        - 이미 있는 미답변 질문과 텍스트가 (공백·대소문자 무시) 겹치면 버린다.
        - 알 수 없는 `type`은 버린다(코드가 임의 보정하지 않음).
        업로드 파이프라인이 best-effort로 호출 — 실패는 호출자가 삼킨다.
        """
        open_count = await self._repo.count_unanswered_by_user(user_id)
        if open_count >= _MAX_OPEN_QUESTIONS:
            return []

        existing = await self._repo.list_by_user(user_id, answered=False)
        existing_norms = {_normalize(q.text) for q in existing}

        raw = await critic.critique_and_generate_questions(
            chapter_body, latest_transcript, [q.text for q in existing]
        )

        fresh: list[GeneratedQuestion] = []
        seen = set(existing_norms)
        for text, type_str in raw:
            norm = _normalize(text)
            if not norm or norm in seen:
                continue
            try:
                qtype = QuestionType(type_str)
            except ValueError:
                continue
            fresh.append(GeneratedQuestion(text=text.strip(), type=qtype))
            seen.add(norm)
            if len(fresh) >= _MAX_NEW_PER_RUN or open_count + len(fresh) >= _MAX_OPEN_QUESTIONS:
                break

        if not fresh:
            return []
        return await self._repo.create_many(user_id, linked_chapter_id, fresh)
