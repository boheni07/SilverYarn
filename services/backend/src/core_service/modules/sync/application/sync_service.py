"""Sync 유스케이스 — sync-contract.md §2(비동기 처리 계약)의 서버측.

`start_upload_session()`이 sync_sessions 행 생성과 arq 잡 enqueue를 함께 책임진다
— 이 둘은 "업로드 접수"라는 하나의 유스케이스이므로 API 레이어에 흩어놓지 않는다.
실제 파이프라인 실행(STT/LLM/Qdrant/Neo4j)은 worker.py + UploadPipelineService가
맡는다 — 이 서비스는 접수와 상태 조회만 담당한다.
"""

import uuid

from arq.connections import ArqRedis

from core_service.core.errors import ApiError
from core_service.modules.sync.domain.sync_session import SyncDirection, SyncSession
from core_service.modules.sync.infrastructure.sync_repository import SyncSessionRepository


class SyncService:
    def __init__(self, repo: SyncSessionRepository, arq_pool: ArqRedis):
        self._repo = repo
        self._pool = arq_pool

    async def start_upload_session(
        self,
        device_id: uuid.UUID,
        user_id: uuid.UUID,
        checksum: str,
        raw_audio_ref: str,
        transcript_on_device: str,
        mode: str | None = None,
        device_session_id: str | None = None,
        turn_id: int | None = None,
    ) -> tuple[SyncSession, str]:
        """POST /sync/upload — sync-contract.md §2.1. (SyncSession, job_id) 튜플 반환."""
        session = await self._repo.create(
            device_id=device_id, direction=SyncDirection.UPLOAD, checksum=checksum
        )
        job = await self._pool.enqueue_job(
            "process_upload",
            session_id=str(session.id),
            user_id=str(user_id),
            raw_audio_ref=raw_audio_ref,
            transcript_on_device=transcript_on_device,
            mode=mode,
            device_session_id=device_session_id,
            turn_id=turn_id,
        )
        # job이 None이면 arq의 잡 중복제거(_job_id 미사용 시 거의 발생 안 함)로 이미
        # 같은 잡이 큐에 있다는 뜻 — 이 경우도 세션은 이미 만들어졌으니 실패로 보지 않는다.
        job_id = job.job_id if job is not None else f"dedup_{session.id}"
        return session, job_id

    async def get_session_status(self, session_id: uuid.UUID) -> SyncSession:
        session = await self._repo.get_by_id(session_id)
        if session is None:
            raise ApiError("NOT_FOUND", f"동기화 세션({session_id})을 찾을 수 없습니다.")
        return session

    async def list_sessions_for_device(self, device_id: uuid.UUID) -> list[SyncSession]:
        """apps/admin 동기화 모니터링(devices/{deviceId}/sync-sessions) — 관리자가 기기
        단위로 최근 동기화 이력을 훑어보는 용도. GET /sync/sessions/{id}(기기 자신의
        폴링용, Device Token 인증)와는 별개의 어드민 조회 경로다."""
        return await self._repo.list_by_device(device_id)
