"""Sync 유스케이스 — sync-contract.md §2(비동기 처리 계약)의 서버측 골격.

TODO(다음 스프린트): 실제 잡 큐 enqueue(arq), Whisper 재전사 → 지식화(Neo4j/Qdrant)
→ vLLM 윤문 파이프라인은 미구현. 지금은 sync_sessions 행 생성 + 202 응답까지만 골격화.
"""

import uuid

from core_service.core.errors import ApiError
from core_service.modules.sync.domain.sync_session import SyncDirection, SyncSession
from core_service.modules.sync.infrastructure.sync_repository import SyncSessionRepository


class SyncService:
    def __init__(self, repo: SyncSessionRepository):
        self._repo = repo

    async def start_upload_session(self, device_id: uuid.UUID, checksum: str) -> SyncSession:
        """POST /sync/upload — sync-contract.md §2.1. 실제 파일 저장·잡 enqueue는 TODO."""
        session = await self._repo.create(
            device_id=device_id, direction=SyncDirection.UPLOAD, checksum=checksum
        )
        # TODO: await enqueue_job("process_upload", session_id=session.id) — core_service.worker
        return session

    async def get_session_status(self, session_id: uuid.UUID) -> SyncSession:
        session = await self._repo.get_by_id(session_id)
        if session is None:
            raise ApiError("NOT_FOUND", f"동기화 세션({session_id})을 찾을 수 없습니다.")
        return session
