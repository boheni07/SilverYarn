"""Publication 도메인 엔티티 — schema.md §3.17 `publications` 테이블 매핑.

`chapters`/`chapter_revisions`와 달리 이 엔티티 자체는 PII 자유텍스트 컬럼이 없다
(완성본은 MinIO 오브젝트로 저장되고 `storage_ref`는 내부 키일 뿐). 원문(챕터 body_text)은
`BookBuilderService`가 조판 시점에만 잠깐 복호화해서 쓰고 이 테이블엔 남기지 않는다.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class PublicationFormat(StrEnum):
    HARDCOVER_PDF = "hardcover_pdf"
    EPUB = "epub"


class PublicationStatus(StrEnum):
    REQUESTED = "requested"
    PROCESSING = "processing"
    READY = "ready"
    DELIVERED = "delivered"


@dataclass
class Publication:
    id: UUID
    user_id: UUID
    format: PublicationFormat
    status: PublicationStatus
    storage_ref: str | None
    requested_at: datetime
    completed_at: datetime | None
