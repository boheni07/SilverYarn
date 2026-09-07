"""비동기 잡 워커 진입점 (arq) — sync-contract.md §2 비동기 처리 계약의 실행측.

실행: arq core_service.worker.WorkerSettings

TODO(다음 스프린트): 실제 잡 함수(process_upload)에서
  Whisper Large-v3 재전사 → 지식추출(Neo4j/Qdrant) → vLLM 윤문 → Compaction Engine
파이프라인(design.md §2.11, workflow-diagrams.md §3/§4)을 구현한다.
지금은 sync_sessions.status를 성공으로 표시하는 최소 골격만 둔다.
"""

import uuid
from typing import Any

from arq.connections import RedisSettings

from core_service.core.config import get_settings

settings = get_settings()


async def process_upload(ctx: dict[str, Any], session_id: str) -> None:
    """POST /sync/upload로 등록된 세션을 처리한다 (골격).

    실제 구현 시 core_service.modules.sync.infrastructure.sync_repository로
    상태를 success/failed로 갱신하고, author/care 모듈의 파이프라인을 호출한다.
    """
    _ = uuid.UUID(session_id)  # 형식 검증만
    # TODO: 실제 파이프라인 호출


class WorkerSettings:
    functions = [process_upload]
    redis_settings = RedisSettings(host=settings.redis_host, port=settings.redis_port)
