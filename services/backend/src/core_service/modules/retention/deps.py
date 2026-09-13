"""retention 모듈의 공개 조합 지점 — family_members/deps.py와 동일한 패턴."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core_service.core.clients.graph_client import GraphClient
from core_service.core.clients.vectordb_client import VectorDBClient
from core_service.core.db import get_db
from core_service.modules.care.infrastructure.conversation_chunk_repository import (
    ConversationChunkRepository,
)
from core_service.modules.retention.application.retention_policy_service import (
    RetentionPolicyService,
)
from core_service.modules.retention.application.retention_purge_service import (
    RetentionPurgeService,
)
from core_service.modules.retention.infrastructure.retention_policy_repository import (
    RetentionPolicyRepository,
)


def get_retention_policy_service(session: AsyncSession = Depends(get_db)) -> RetentionPolicyService:
    return RetentionPolicyService(RetentionPolicyRepository(session))


def build_retention_purge_service(session: AsyncSession) -> RetentionPurgeService:
    """worker.py 전용 — FastAPI Depends가 아니라 arq cron job에서 직접 호출한다
    (요청 스코프 세션이 없으므로 `Depends(get_db)`를 못 쓴다, `process_upload`와 동일한 사정)."""
    return RetentionPurgeService(ConversationChunkRepository(session), VectorDBClient(), GraphClient())
