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
from core_service.modules.author.application.chapter_service import ChapterService
from core_service.modules.author.application.question_service import QuestionService
from core_service.modules.author.deps import get_chapter_service, get_question_service
from core_service.modules.devices.application.device_service import DeviceService
from core_service.modules.devices.deps import get_device_service
from core_service.modules.schedule.application.schedule_item_service import ScheduleItemService
from core_service.modules.schedule.deps import get_schedule_item_service
from core_service.modules.sync.application.sync_service import SyncService
from core_service.modules.sync.domain.sync_session import SyncStatus
from core_service.modules.sync.infrastructure.sync_repository import SyncSessionRepository
from core_service.shared.schemas import DataResponse, PaginatedResponse, Pagination

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
    폴링용)와 달리 device_id/direction까지 보여준다. device_display_id는 sync 모듈이
    devices 테이블을 직접 조인하지 않고(deps.py를 통한 애플리케이션 레벨 조합) 라우터에서
    채워 넣는다 — 기기가 삭제됐다면(흔치 않지만 FK CASCADE로 가능) null."""

    id: uuid.UUID
    device_id: uuid.UUID
    device_display_id: str | None = None
    direction: str
    status: str
    retry_count: int
    started_at: datetime
    finished_at: datetime | None


class ChapterUpdateResponse(BaseModel):
    chapter_id: uuid.UUID
    chapter_no: int
    period: str
    summary: str
    keywords: list[str]


class PriorityQuestionResponse(BaseModel):
    question_id: uuid.UUID
    linked_chapter_id: uuid.UUID | None
    text: str
    type: str


class ScheduleItemDownloadResponse(BaseModel):
    id: uuid.UUID
    kind: str
    due_at: datetime
    description: str | None


class SyncDownloadResponse(BaseModel):
    sync_version: str
    chapter_updates: list[ChapterUpdateResponse]
    priority_questions: list[PriorityQuestionResponse]
    schedule_items: list[ScheduleItemDownloadResponse]


_SYNC_VERSION_FORMAT = "sync_%Y%m%d_%H%M%S"


def _new_sync_version() -> str:
    return datetime.now(UTC).strftime(_SYNC_VERSION_FORMAT)


def _parse_since(since: str | None) -> datetime | None:
    """`since`는 이전 응답의 `sync_version`을 그대로 돌려받는 불투명 커서다
    (sync-contract.md §5) — 이 서버가 발급하는 형식(`_SYNC_VERSION_FORMAT`)만
    해석할 수 있으면 되고, 없거나 형식이 안 맞으면 전체 스냅샷으로 안전하게
    폴백한다(데이터 유실보다는 중복이 낫다)."""
    if not since:
        return None
    try:
        return datetime.strptime(since, _SYNC_VERSION_FORMAT).replace(tzinfo=UTC)
    except ValueError:
        return None


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


@router.get("/sessions", response_model=PaginatedResponse[SyncSessionResponse])
async def list_sessions(
    page: int = 1,
    page_size: int = 20,
    device_id: uuid.UUID | None = None,
    status: SyncStatus | None = None,
    service: SyncService = Depends(_service),
    device_service: DeviceService = Depends(get_device_service),
    # Admin — TODO: role 체크 강화 (devices.py list_user_devices와 동일 패턴)
    _ctx: AuthContext = Depends(require_auth),
) -> PaginatedResponse[SyncSessionResponse]:
    """apps/admin 동기화 모니터링 화면 — 공통 조회 경로.

    `device_id`를 주면 기기 하나의 이력(devices → sync-monitor 화면), 생략하면
    "전체 기기 통합 모니터링"(신규, 2026-09-08)이 된다. `status`로 성공/실패/재시도중만
    골라볼 수 있다. 위 /sessions/{session_id}(기기 자신의 폴링용, Device Token 인증)와는
    별개의 관리자 조회 경로다.

    device_display_id는 이 페이지에 등장하는 기기 ID들만 모아 devices 모듈에
    한 번의 IN 쿼리로 물어본다(N+1 아님) — sync 모듈이 devices 테이블을 직접
    조인하지 않는다는 원칙(structure.md §2)을 지키면서도 매 세션마다 개별
    조회하지 않도록.
    """
    sessions, total = await service.list_sessions(
        page=page, page_size=page_size, device_id=device_id, status=status
    )
    display_ids = await device_service.get_display_ids([s.device_id for s in sessions])
    return PaginatedResponse(
        data=[
            SyncSessionResponse(
                id=s.id,
                device_id=s.device_id,
                device_display_id=display_ids.get(s.device_id),
                direction=s.direction.value,
                status=s.status.value,
                retry_count=s.retry_count,
                started_at=s.started_at,
                finished_at=s.finished_at,
            )
            for s in sessions
        ],
        pagination=Pagination(page=page, page_size=page_size, total=total),
    )


@router.get("/download", response_model=DataResponse[SyncDownloadResponse])
async def download(
    device_id: uuid.UUID,
    since: str | None = None,
    device_service: DeviceService = Depends(get_device_service),
    chapter_service: ChapterService = Depends(get_chapter_service),
    question_service: QuestionService = Depends(get_question_service),
    schedule_service: ScheduleItemService = Depends(get_schedule_item_service),
    _device: str = Depends(require_device_token),
) -> DataResponse[SyncDownloadResponse]:
    """sync-contract.md §5 — 증분 다운로드.

    ⚠️ sync-contract.md §5 원문은 `since` 하나뿐이고 호출 주체(어느 사용자 것을
    내려줄지)를 식별할 파라미터가 없었다 — POST /sync/upload가 body의 device_id로
    device→user_id 신뢰사슬을 쓰는 것과 같은 이유(Device Token 자체는 아직 특정
    기기를 검증하지 못하는 스텁, core/auth.py)로 `device_id` 쿼리 파라미터를
    추가했다(sync-contract.md v0.3에 반영).

    chapter_updates의 summary/keywords는 design.md §2.11 Compaction Engine(AI
    요약 파이프라인, 이 세션 스코프 밖)이 아직 없어 body_text 원문/빈 배열로
    대체한다 — 실 파이프라인이 생기면 이 자리만 교체.
    """
    device = await device_service.get_device(device_id)
    since_dt = _parse_since(since)

    chapters = await chapter_service.list_chapter_updates_for_user(device.user_id, since_dt)
    questions = await question_service.list_priority_questions_for_user(device.user_id, since_dt)
    schedule_items = await schedule_service.list_pending_schedule_items_for_user(device.user_id)

    return DataResponse(
        data=SyncDownloadResponse(
            sync_version=_new_sync_version(),
            chapter_updates=[
                ChapterUpdateResponse(
                    chapter_id=c.id,
                    chapter_no=c.chapter_no,
                    period=c.period.value,
                    summary=c.body_text,
                    keywords=[],
                )
                for c in chapters
            ],
            priority_questions=[
                PriorityQuestionResponse(
                    question_id=q.id,
                    linked_chapter_id=q.linked_chapter_id,
                    text=q.text,
                    type=q.type.value,
                )
                for q in questions
            ],
            schedule_items=[
                ScheduleItemDownloadResponse(
                    id=s.id, kind=s.kind.value, due_at=s.due_at, description=s.description
                )
                for s in schedule_items
            ],
        )
    )
