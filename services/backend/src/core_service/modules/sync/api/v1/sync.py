"""sync 리소스 라우터 — sync-contract.md §2/§5 시그니처를 그대로 구현.

⚠️ 골격 단계: 업로드 파일 실제 저장, Whisper/vLLM/Qdrant/Neo4j 파이프라인은 TODO.
지금은 sync_sessions 행 생성 + 202 Accepted 응답 계약만 검증 가능하다.
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core_service.core.auth import require_device_token
from core_service.core.db import get_db
from core_service.modules.sync.application.sync_service import SyncService
from core_service.modules.sync.infrastructure.sync_repository import SyncSessionRepository
from core_service.shared.schemas import DataResponse

router = APIRouter(prefix="/sync", tags=["sync"])


class SyncUploadRequest(BaseModel):
    """실제로는 multipart(오디오+전사+메타)이나, 골격 단계에서는 체크섬만 받는다."""

    device_id: uuid.UUID
    checksum: str


class SyncUploadAccepted(BaseModel):
    session_id: uuid.UUID
    job_id: str
    status: str = "queued"


class SyncSessionStatusResponse(BaseModel):
    session_id: uuid.UUID
    status: str
    retry_count: int
    started_at: datetime
    finished_at: datetime | None


def _service(session: AsyncSession = Depends(get_db)) -> SyncService:
    return SyncService(SyncSessionRepository(session))


@router.post("/upload", response_model=DataResponse[SyncUploadAccepted], status_code=202)
async def upload(
    body: SyncUploadRequest,
    response: Response,
    service: SyncService = Depends(_service),
    _device: str = Depends(require_device_token),
) -> DataResponse[SyncUploadAccepted]:
    """sync-contract.md §2.1 — 즉시 202 Accepted, 처리는 비동기."""
    session = await service.start_upload_session(device_id=body.device_id, checksum=body.checksum)
    response.headers["Location"] = f"/api/v1/sync/sessions/{session.id}"
    return DataResponse(data=SyncUploadAccepted(session_id=session.id, job_id=f"job_{session.id}"))


@router.get("/sessions/{session_id}", response_model=DataResponse[SyncSessionStatusResponse])
async def get_session_status(
    session_id: uuid.UUID,
    service: SyncService = Depends(_service),
    _device: str = Depends(require_device_token),
) -> DataResponse[SyncSessionStatusResponse]:
    """sync-contract.md §2.2 — 클라이언트 폴링용."""
    session = await service.get_session_status(session_id)
    return DataResponse(
        data=SyncSessionStatusResponse(
            session_id=session.id,
            status=session.status.value,
            retry_count=session.retry_count,
            started_at=session.started_at,
            finished_at=session.finished_at,
        )
    )


@router.get("/download")
async def download(
    since: str | None = None,
    _device: str = Depends(require_device_token),
) -> dict:
    """sync-contract.md §5 — 증분 다운로드. 파이프라인 미구현이라 빈 스냅샷 골격만 반환.

    TODO: chapter_updates/priority_questions/schedule_items 실제 조회(design.md §4.3 예시 형식).
    """
    return {
        "data": {
            "sync_version": f"sync_{datetime.now():%Y%m%d_%H%M%S}",
            "chapter_updates": [],
            "priority_questions": [],
            "schedule_items": [],
        }
    }
