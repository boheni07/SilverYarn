"""Question 도메인 엔티티 — schema.md §3.9 `questions`(회고 질문 큐) 매핑.

author 모듈 소속인 이유: `linked_chapter_id`로 chapters를 참조하고(연대기 탭별
질문 필터링, schema.md v1.1), GET /sync/download의 `priority_questions`(design.md
§4.3)가 이 테이블의 서브셋이라 — 별도 최상위 모듈로 쪼개기보다 chapters와 같은
생애사 콘텐츠를 다루는 author 모듈에 둔다(schedule_items가 "비서 모드"로
독립 모듈인 것과 달리, questions는 자서전 인터뷰 흐름의 산출물이라는 차이).

⚠️ 질문 자동 생성(작가 엔진이 다음 인터뷰 질문을 뽑아 이 테이블에 채우는 흐름)은
아직 미구현 — 이 모듈은 읽기(`list_unanswered_by_user`) 경로만 제공한다. 질문을
실제로 만드는 쪽(워커/온프레미스 LLM 파이프라인)은 이 세션 스코프 밖.
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
