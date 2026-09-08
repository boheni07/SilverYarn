"""sync 리소스 라우터 — sync-contract.md §2/§5 시그니처를 구현.

⚠️ 업로드는 실제로 multipart(오디오 파일+전사+메타)여야 하나, 오디오 자체는
Presigned URL로 MinIO에 먼저 올린 뒤(sync-contract.md §4와 유사한 흐름을 §2에도
적용해야 함 — TODO) 그 참조(raw_audio_ref)만 이 엔드포인트에 JSON으로 보낸다고
가정했다. 지금은 오디오 업로드 자체가 미구현이라 raw_audio_ref를 클라이언트가
문자열로 직접 넘긴다.
"""

import uuid
from datetime import UTC, datetime

from arq.connections import ArqRedis
from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core_service.core.auth import AuthContext, require_auth, require_device_token
from core_service.core.db import get_db
from core_service.core.queue import get_arq_pool
from core_service.modules.devices.application.device_service import DeviceService
from core_service.modules.devices.deps import get_device_service
from core_service.modules.sync.application.sync_service import SyncService
from core_service.modules.sync.infrastructure.sync_repository import SyncSessionRepository
from core_service.shared.schemas import DataResponse

router = APIRouter(prefix="/sync", tags=["sync"])


class SyncUploadRequest(BaseModel):
    device_id: uuid.UUID
    checksum: str
    raw_audio_ref: str
    transcript_on_device: str
    mode: str | None = None  # ConversationMode 값(author/care/assist), 문자열로 받아 워커에 그대로 전달
    device_session_id: str | None = None
    turn_id: int | None = None


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


class SyncSessionResponse(BaseModel):
    """apps/admin 동기화 모니터링용 목록 응답 — 위 SyncSessionStatusResponse(기기 자신의
    폴링용)와 달리 device_id/direction까지 보여준다."""

    id: uuid.UUID
    device_id: uuid.UUID
    direction: str
    status: str
    retry_count: int
    started_at: datetime
    finished_at: datetime | None


def _service(session: AsyncSession = Depends(get_db), pool: ArqRedis = Depends(get_arq_pool)) -> SyncService:
    return SyncService(SyncSessionRepository(session), pool)


@router.post("/upload", response_model=DataResponse[SyncUploadAccepted], status_code=202)
async def upload(
    body: SyncUploadRequest,
    response: Response,
    service: SyncService = Depends(_service),
    device_service: DeviceService = Depends(get_device_service),
    _device: str = Depends(require_device_token),
) -> DataResponse[SyncUploadAccepted]:
    """sync-contract.md §2.1 — 즉시 202 Accepted, 처리는 worker.py의 process_upload 잡.

    user_id는 클라이언트가 주장하게 두지 않는다 — device_id로 devices 모듈에서
    조회한다(Device Token → 기기 → 사용자로 신뢰 사슬을 유지).
    """
    device = await device_service.get_device(body.device_id)  # 없으면 NOT_FOUND
    session, job_id = await service.start_upload_session(
        device_id=body.device_id,
        user_id=device.user_id,
        checksum=body.checksum,
        raw_audio_ref=body.raw_audio_ref,
        transcript_on_device=body.transcript_on_device,
        mode=body.mode,
        device_session_id=body.device_session_id,
        turn_id=body.turn_id,
    )
    response.headers["Location"] = f"/api/v1/sync/sessions/{session.id}"
    return DataResponse(data=SyncUploadAccepted(session_id=session.id, job_id=job_id))


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


@router.get("/sessions", response_model=DataResponse[list[SyncSessionResponse]])
async def list_sessions(
    device_id: uuid.UUID,
    service: SyncService = Depends(_service),
    # Admin — TODO: role 체크 강화 (devices.py list_user_devices와 동일 패턴)
    _ctx: AuthContext = Depends(require_auth),
) -> DataResponse[list[SyncSessionResponse]]:
    """apps/admin 동기화 모니터링 화면 — 기기 하나의 최근 동기화 이력을 조회한다.

    위 /sessions/{session_id}(기기 자신의 폴링용, Device Token 인증)와는 별개의
    관리자 조회 경로다. "전체 기기 통합 모니터링"은 아직 없다 — 기기 단위 조회만
    지원(apps/admin/README.md "아직 안 된 것" 참조).
    """
    sessions = await service.list_sessions_for_device(device_id)
    return DataResponse(
        data=[
            SyncSessionResponse(
                id=s.id,
                device_id=s.device_id,
                direction=s.direction.value,
                status=s.status.value,
                retry_count=s.retry_count,
                started_at=s.started_at,
                finished_at=s.finished_at,
            )
            for s in sessions
        ]
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
            "sync_version": f"sync_{datetime.now(UTC):%Y%m%d_%H%M%S}",
            "chapter_updates": [],
            "priority_questions": [],
            "schedule_items": [],
        }
    }
