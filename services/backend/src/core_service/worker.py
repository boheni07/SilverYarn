"""비동기 잡 워커 진입점 (arq) — sync-contract.md §2 비동기 처리 계약의 실행측.

실행: arq core_service.worker.WorkerSettings

FastAPI 프로세스와 달리 요청 스코프의 `Depends(get_db)`가 없으므로, 잡 함수 안에서
직접 세션을 열고 커밋/롤백까지 책임진다(core/db.py의 get_db() 주석 참조 — 커밋을
빼먹으면 아무것도 저장되지 않는다).
"""

import logging
import uuid
from typing import Any

from arq.connections import RedisSettings

from core_service.core.clients.embedding_client import EmbeddingClient
from core_service.core.clients.graph_client import GraphClient
from core_service.core.clients.llm_client import LLMClient
from core_service.core.clients.stt_client import STTClient
from core_service.core.clients.vectordb_client import VectorDBClient
from core_service.core.config import get_settings
from core_service.core.db import get_session_factory
from core_service.modules.author.application.chapter_service import ChapterService
from core_service.modules.author.infrastructure.chapter_repository import ChapterRepository
from core_service.modules.author.infrastructure.chapter_revision_repository import (
    ChapterRevisionRepository,
)
from core_service.modules.care.application.conversation_chunk_service import (
    ConversationChunkService,
)
from core_service.modules.care.domain.conversation_chunk import ConversationMode
from core_service.modules.care.infrastructure.conversation_chunk_repository import (
    ConversationChunkRepository,
)
from core_service.modules.sync.application.upload_pipeline_service import (
    UploadPipelineInput,
    UploadPipelineService,
)
from core_service.modules.sync.infrastructure.sync_repository import SyncSessionRepository

settings = get_settings()
logger = logging.getLogger(__name__)


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
    session_factory = get_session_factory()
    async with session_factory() as db_session:
        try:
            pipeline = UploadPipelineService(
                sync_repo=SyncSessionRepository(db_session),
                chunk_service=ConversationChunkService(ConversationChunkRepository(db_session)),
                chapter_service=ChapterService(
                    ChapterRepository(db_session), ChapterRevisionRepository(db_session)
                ),
                stt_client=STTClient(),
                embedding_client=EmbeddingClient(),
                llm_client=LLMClient(),
                vectordb_client=VectorDBClient(),
                graph_client=GraphClient(),
            )
            await pipeline.run(
                UploadPipelineInput(
                    sync_session_id=uuid.UUID(session_id),
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
            raise


class WorkerSettings:
    functions = [process_upload]
    redis_settings = RedisSettings(host=settings.redis_host, port=settings.redis_port)
