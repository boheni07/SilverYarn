"""Chapter/ChapterRevision 도메인 엔티티 — schema.md §5 `chapters`/`chapter_revisions` 매핑.

`chapter_revisions`는 감수 시점에만 생성된다(3차 검증 M-5 정정, workflow-diagrams.md §7).
작가 엔진(§4)이 초안을 생성/갱신할 때는 `chapters`만 draft/in_review로 저장하고,
가족이 실제로 승인/반려할 때 비로소 이 모듈의 `review_chapter` 유스케이스가
`chapter_revisions` 행을 만든다 — 감수 전에 만들면 안 되는 이유는 schema.md상
`action`(approved/rejected) 컬럼이 NOT NULL이라 감수 결과 없이는 애초에 유효한
행을 만들 수 없기 때문이다.
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


class RevisionAction(StrEnum):
    APPROVED = "approved"
    REJECTED = "rejected"


# 감수(review_chapter)를 받을 수 있는 상태 — 이미 확정/반려된 챕터를 재감수하려면
# 먼저 새 초안(draft/in_review)으로 되돌아가야 한다(워크플로우 §7).
REVIEWABLE_STATUSES = frozenset({ChapterStatus.DRAFT, ChapterStatus.IN_REVIEW})


@dataclass(frozen=True)
class ChapterCompaction:
    """온디바이스 FTS5(`autobiography_fts`)로 내려보낼 챕터 요약·키워드 — design §2.11 4단계.

    `source_version`은 이 요약이 어느 `Chapter.version`에서 만들어졌는지다. `Chapter.version`과
    다르면 요약이 stale이므로 파이프라인이 재계산한다.
    """

    summary: str
    keywords: list[str]
    source_version: int


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
    compaction: ChapterCompaction | None = None

    @property
    def compaction_is_stale(self) -> bool:
        """요약이 없거나 현재 본문 버전보다 뒤처졌으면 True."""
        return self.compaction is None or self.compaction.source_version != self.version

    def ensure_reviewable(self) -> None:
        """비즈니스 규칙: draft/in_review 상태만 감수 가능(schema.md chapter_status)."""
        if self.status not in REVIEWABLE_STATUSES:
            raise ValueError(
                f"챕터가 감수 가능한 상태가 아닙니다(현재: {self.status.value}). "
                "이미 확정/반려된 챕터는 재작성 후 다시 감수해야 합니다."
            )


@dataclass
class ChapterRevision:
    id: UUID
    chapter_id: UUID
    version: int
    body_text_snapshot: str
    reviewer_id: UUID | None
    review_comment: str | None
    action: RevisionAction
    created_at: datetime
