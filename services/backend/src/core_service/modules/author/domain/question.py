"""Question 도메인 엔티티 — schema.md §3.9 `questions`(회고 질문 큐) 매핑.

author 모듈 소속인 이유: `linked_chapter_id`로 chapters를 참조하고(연대기 탭별
질문 필터링, schema.md v1.1), GET /sync/download의 `priority_questions`(design.md
§4.3)가 이 테이블의 서브셋이라 — 별도 최상위 모듈로 쪼개기보다 chapters와 같은
생애사 콘텐츠를 다루는 author 모듈에 둔다(schedule_items가 "비서 모드"로
독립 모듈인 것과 달리, questions는 자서전 인터뷰 흐름의 산출물이라는 차이).

질문 자동 생성(Critic Agent)은 `QuestionService.generate_followups`가 담당한다 —
업로드 파이프라인이 챕터를 갱신한 뒤 best-effort로 호출해, 온프레미스 vLLM이
서사 완성도(Fact/Emotion/Relation/Reflection 4축)를 채점하고 부족 영역을 메울
심층 질문 Top-3을 이 큐에 넣는다(design.md §2.11 3단계, workflow-diagrams.md §4).
"""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class QuestionType(StrEnum):
    NEW_TOPIC = "new_topic"
    FOLLOW_UP = "follow_up"


@dataclass
class Question:
    id: UUID
    user_id: UUID
    linked_chapter_id: UUID | None
    text: str
    type: QuestionType
    answered: bool
    created_at: datetime


@dataclass(frozen=True)
class GeneratedQuestion:
    """Critic Agent(vLLM)가 만든 질문 초안 — 아직 DB에 안 들어간 상태."""

    text: str
    type: QuestionType
