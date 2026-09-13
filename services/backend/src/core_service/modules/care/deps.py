"""care 모듈의 공개 조합 지점 — family_members/deps.py와 동일한 패턴.

sync 모듈의 UploadPipelineService가 ConversationChunkService가 필요할 때 이 파일만
import한다.
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core_service.core.db import get_db
from core_service.modules.care.application.conversation_chunk_service import (
    ConversationChunkService,
)
from core_service.modules.care.infrastructure.conversation_chunk_repository import (
    ConversationChunkRepository,
)
from core_service.modules.retention.application.retention_policy_service import (
    RetentionPolicyService,
)
from core_service.modules.retention.deps import get_retention_policy_service


def get_conversation_chunk_service(
    session: AsyncSession = Depends(get_db),
    retention: RetentionPolicyService = Depends(get_retention_policy_service),
) -> ConversationChunkService:
    return ConversationChunkService(ConversationChunkRepository(session), retention)
