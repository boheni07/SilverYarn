"""비동기 잡 워커 진입점 (arq) — sync-contract.md §2 비동기 처리 계약의 실행측.

실행: arq core_service.worker.WorkerSettings

FastAPI 프로세스와 달리 요청 스코프의 `Depends(get_db)`가 없으므로, 잡 함수 안에서
직접 세션을 열고 커밋/롤백까지 책임진다(core/db.py의 get_db() 주석 참조 — 커밋을
빼먹으면 아무것도 저장되지 않는다).

⚠️ **sync_sessions 상태 갱신은 별도의 독립 세션을 쓴다**: 실제 DB로 엔드투엔드
테스트하다가, 파이프라인 세션이 flush 실패로 poisoned(PendingRollbackError) 된
뒤 같은 세션으로 상태를 failed로 쓰려다 2차 예외가 나 원인이 가려지는 문제를
발견했다. `_update_sync_status()`가 매번 새 세션을 열어 즉시 커밋하므로, 파이프라인
쪽 트랜잭션이 어떻게 되든 상태 기록은 항상 남는다.
"""

import logging
import uuid
from typing import Any

from arq import cron
from arq.connections import RedisSettings

from core_service.core import model_registry  # noqa: F401  (Base.metadata에 전 테이블 등록)
from core_service.core.clients.embedding_client import EmbeddingClient
from core_service.core.clients.graph_client import GraphClient
from core_service.core.clients.llm_client import LLMClient
from core_service.core.clients.storage_client import StorageClient
from core_service.core.clients.stt_client import STTClient
from core_service.core.clients.vectordb_client import VectorDBClient
from core_service.core.config import get_settings
from core_service.core.db import get_session_factory
from core_service.modules.author.application.chapter_service import ChapterService
from core_service.modules.author.application.question_service import QuestionService
from core_service.modules.author.infrastructure.chapter_repository import ChapterRepository
from core_service.modules.author.infrastructure.chapter_revision_repository import (
    ChapterRevisionRepository,
)
from core_service.modules.author.infrastructure.question_repository import QuestionRepository
from core_service.modules.care.application.conversation_chunk_service import (
    ConversationChunkService,
)
from core_service.modules.care.domain.conversation_chunk import ConversationMode
from core_service.modules.care.infrastructure.conversation_chunk_repository import (
    ConversationChunkRepository,
)
from core_service.modules.photos.application.photo_service import PhotoService
from core_service.modules.photos.infrastructure.photo_repository import PhotoRepository
from core_service.modules.sync.application.upload_pipeline_service import (
    UploadPipelineInput,
    UploadPipelineService,
)
from core_service.modules.sync.domain.sync_session import SyncStatus
from core_service.modules.sync.infrastructure.sync_repository import SyncSessionRepository

settings = get_settings()
logger = logging.getLogger(__name__)


async def _update_sync_status(session_id: uuid.UUID, status: SyncStatus) -> None:
    """독립 세션 + 즉시 커밋 — 파이프라인 세션의 성공/실패와 무관하게 항상 남는다."""
    session_factory = get_session_factory()
    async with session_factory() as status_session:
        try:
            await SyncSessionRepository(status_session).update_status(session_id, status)
            await status_session.commit()
        except Exception:
            logger.exception(
                "sync_sessions 상태 갱신 자체가 실패 — session_id=%s, status=%s", session_id, status
            )
            await status_session.rollback()


async def process_upload(
    ctx: dict[str, Any],
    session_id: str,
    user_id: str,
    raw_audio_ref: str,
    transcript_on_device: str,
    mode: str | None = None,
    device_session_id: str | None = None,
    turn_id: int | None = None,
) -> None:
    """POST /sync/upload로 등록된 세션을 처리한다.

    인자는 sync API의 `SyncUploadRequest`에서 그대로 넘어온다(uuid/enum은 arq
    직렬화 편의를 위해 문자열로 받아 여기서 다시 파싱).
    """
    _ = ctx
    sync_session_id = uuid.UUID(session_id)
    session_factory = get_session_factory()
    async with session_factory() as db_session:
        try:
            pipeline = UploadPipelineService(
                chunk_service=ConversationChunkService(ConversationChunkRepository(db_session)),
                chapter_service=ChapterService(
                    ChapterRepository(db_session), ChapterRevisionRepository(db_session)
                ),
                question_service=QuestionService(QuestionRepository(db_session)),
                stt_client=STTClient(),
                embedding_client=EmbeddingClient(),
                llm_client=LLMClient(),
                vectordb_client=VectorDBClient(),
                graph_client=GraphClient(),
            )
            await pipeline.run(
                UploadPipelineInput(
                    sync_session_id=sync_session_id,
                    user_id=uuid.UUID(user_id),
                    raw_audio_ref=raw_audio_ref,
                    transcript_on_device=transcript_on_device,
                    mode=ConversationMode(mode) if mode else None,
                    device_session_id=device_session_id,
                    turn_id=turn_id,
                )
            )
            await db_session.commit()
        except Exception:
            logger.exception("process_upload 잡 실패 — session_id=%s", session_id)
            await db_session.rollback()
            await _update_sync_status(sync_session_id, SyncStatus.FAILED)
            raise
        else:
            await _update_sync_status(sync_session_id, SyncStatus.SUCCESS)


async def cleanup_orphan_photos(ctx: dict[str, Any]) -> None:
    """sync-contract.md §4 orphan cleanup — 매시 정각 실행(WorkerSettings.cron_jobs).

    3단계 확인 콜백이 24시간 넘게 안 온 `pending_upload` 사진 행을 정리한다.
    process_upload와 달리 실패해도 sync_sessions처럼 상태를 기록할 대상이 없어
    (photos에는 그런 상태 이력 컬럼이 없음) 그냥 로그만 남기고 다음 시간에 재시도.
    """
    _ = ctx
    session_factory = get_session_factory()
    async with session_factory() as db_session:
        try:
            service = PhotoService(PhotoRepository(db_session), StorageClient())
            cleaned = await service.cleanup_orphan_pending_uploads()
            await db_session.commit()
            if cleaned:
                logger.info("photos orphan cleanup — %d건 정리", cleaned)
        except Exception:
            logger.exception("photos orphan cleanup 잡 실패")
            await db_session.rollback()
            raise


class WorkerSettings:
    functions = [process_upload]
    cron_jobs = [cron(cleanup_orphan_photos, hour=set(range(24)), minute=0)]
    redis_settings = RedisSettings(host=settings.redis_host, port=settings.redis_port)
