"""Photo 도메인 엔티티 — schema.md §5 `photos` 테이블 매핑.

⚠️ 골격 단계: Repository/Service/API 미구현(photos/__init__.py 참조).
"""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class UploaderType(StrEnum):
    FAMILY = "family"
    SELF = "self"


class RecallStatus(StrEnum):
    PENDING = "pending"
    COMPLETED = "completed"


class PlacementStatus(StrEnum):
    PROPOSED = "proposed"
    CONFIRMED = "confirmed"


class QualityFlag(StrEnum):
    OK = "ok"
    BLURRY = "blurry"
    INAPPROPRIATE = "inappropriate"
    UNREVIEWED = "unreviewed"


@dataclass
class Photo:
    id: UUID
    user_id: UUID
    uploader_type: UploaderType
    storage_ref: str
    caption: str | None
    year_tag: int | None
    recall_status: RecallStatus
    placement_status: PlacementStatus
    inline_position: str | None
    linked_chunk_id: UUID | None
    linked_chapter_id: UUID | None
    quality_flag: QualityFlag
    width: int | None
    height: int | None
    file_size_kb: int | None
    mime_type: str | None
    uploaded_at: datetime
