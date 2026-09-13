"""보유기간 만료 대화 청크 파기(purge) 오케스트레이션 — decisions.md #56(Q5).

`care.ConversationChunkRepository.list_expired_unpurged()`로 배치를 가져와,
각 청크마다 Qdrant(임베딩)·Neo4j(그래프 노드)·Postgres(원본 텍스트 redaction)
순서로 지운다 — 외부 저장소를 먼저 지우는 이유는 `UserErasureService`와 동일하다
(외부 삭제는 멱등이라 실패해도 재시도 안전, Postgres를 먼저 지우면 재시도에 필요한
chunk_id/embedding_id/graph_node_ref를 잃는다).

이 서비스는 `care` 모듈에 의존한다(cross-module composition) — sync 모듈의
UploadPipelineService가 이미 같은 패턴으로 care.ConversationChunkService에
의존하고 있어(care/deps.py), pyproject.toml의 import-linter 계약도 모듈 간
의존 자체는 막지 않는다(계층 위반만 막는다).
"""

import logging

from core_service.core.clients.graph_client import GraphClient
from core_service.core.clients.vectordb_client import VectorDBClient
from core_service.modules.care.infrastructure.conversation_chunk_repository import (
    ConversationChunkRepository,
)

logger = logging.getLogger(__name__)


class RetentionPurgeService:
    def __init__(
        self,
        chunk_repo: ConversationChunkRepository,
        vectordb_client: VectorDBClient,
        graph_client: GraphClient,
    ):
        self._chunks = chunk_repo
        self._vectordb = vectordb_client
        self._graph = graph_client

    async def purge_expired_chunks(self, batch_size: int = 100) -> int:
        """만료된 청크 최대 `batch_size`건을 파기하고 처리 건수를 반환한다.

        arq cron job(worker.py)이 매 실행마다 이 메서드를 호출한다 — 한 번의
        실행에서 배치 크기만큼만 처리하는 이유는 대량 만료 시(정책 변경 등)
        한 트랜잭션이 무한정 커지는 걸 막기 위해서다. 다음 스케줄에서 이어서
        처리된다(마이그레이션 0012의 부분 인덱스 덕에 반복 조회 비용이 낮음).
        """
        expired = await self._chunks.list_expired_unpurged(limit=batch_size)
        for chunk in expired:
            if chunk.embedding_id is not None:
                await self._vectordb.delete_chunk_embedding(chunk.id)
            if chunk.graph_node_ref is not None:
                await self._graph.delete_chunk_node(chunk.id)
            await self._chunks.redact_and_mark_purged(chunk.id)
        if expired:
            logger.info("보유기간 만료 대화 청크 파기 완료 — %d건", len(expired))
        return len(expired)
