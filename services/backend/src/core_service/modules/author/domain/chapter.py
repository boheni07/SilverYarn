"""Chapter 도메인 엔티티 — schema.md §5 `chapters` 테이블 매핑.

⚠️ 골격 단계: Repository/Service/API 미구현 — workflow-diagrams.md §4/§7 워크플로우를
따르는 다음 스프린트에서 구현한다. `chapter_revisions`는 감수 시점에만 생성되며
(3차 검증 M-5 정정), 이 모듈이 아직 그 생성 로직을 갖고 있지 않다.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class ChapterPeriod(StrEnum):
    CHILDHOOD = "childhood"
    YOUTH = "youth"
    ADULTHOOD = "adulthood"
    PRESENT = "present"


class ChapterStatus(StrEnum):
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    REJECTED = "rejected"
    CONFIRMED = "confirmed"


@dataclass
class Chapter:
    id: UUID
    user_id: UUID
    chapter_no: int
    title: str
    period: ChapterPeriod
    body_text: str
    status: ChapterStatus
    version: int
    updated_at: datetime
