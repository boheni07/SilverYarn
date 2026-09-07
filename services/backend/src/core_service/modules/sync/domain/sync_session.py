"""SyncSession 도메인 엔티티 — schema.md §5 `sync_sessions` 테이블 매핑.

sync-contract.md §2의 "status" 값(queued/processing/completed/failed/partial)은 API 표현이며,
schema.md의 sync_status enum(success/failed/retrying) 3값과는 표현 레벨이 다르다 —
잡 진행 상태는 이 도메인 밖(아래 JobStatus)에서 별도 추적하고, sync_sessions.status는
잡이 종료된 뒤의 "최종 결과"만 기록한다. TODO(Do 단계): 진행중 상태를 별도 테이블/Redis로
추적할지, sync_status enum을 확장할지 결정 — 지금은 스캐폴딩이라 in-memory 골격만 둔다.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class SyncDirection(StrEnum):
    UPLOAD = "upload"
    DOWNLOAD = "download"


class SyncStatus(StrEnum):
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class SyncSession:
    id: UUID
    device_id: UUID
    direction: SyncDirection
    status: SyncStatus
    checksum: str
    retry_count: int
    started_at: datetime
    finished_at: datetime | None
