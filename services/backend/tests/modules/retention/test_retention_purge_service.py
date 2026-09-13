"""RetentionPurgeService 유닛 테스트 — 페이크 3종(청크 Repository·Qdrant·Neo4j)으로
DB/실 인프라 없이 Application 계층의 호출 순서·조건을 검증한다.

decisions.md #56(Q5, 2026-09-13) — 보유기간 만료 대화 청크 파기 오케스트레이션.
"""

import uuid
from datetime import UTC, datetime, timedelta

from core_service.modules.care.domain.conversation_chunk import ConversationChunk
from core_service.modules.retention.application.retention_purge_service import (
    RetentionPurgeService,
)


def _chunk(
    *,
    embedding_id: str | None = "emb-1",
    graph_node_ref: str | None = "node-1",
    retention_until: datetime | None = None,
    purged_at: datetime | None = None,
) -> ConversationChunk:
    now = datetime.now(UTC)
    return ConversationChunk(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        raw_audio_ref="opus/x.opus",
        transcript_on_device="원본",
        transcript_server="서버본",
        meta_period=None,
        meta_people=None,
        meta_place=None,
        meta_emotion=None,
        meta_prosody=None,
        linked_photo_id=None,
        embedding_id=embedding_id,
        graph_node_ref=graph_node_ref,
        session_id=None,
        turn_id=None,
        mode=None,
        assistant_response=None,
        created_at=now,
        retention_until=retention_until if retention_until is not None else now - timedelta(days=1),
        purged_at=purged_at,
    )


class FakeConversationChunkRepository:
    def __init__(self, expired: list[ConversationChunk]) -> None:
        self._expired = expired
        self.redacted_ids: list[uuid.UUID] = []

    async def list_expired_unpurged(self, limit: int = 100) -> list[ConversationChunk]:
        return self._expired[:limit]

    async def redact_and_mark_purged(self, chunk_id: uuid.UUID) -> None:
        self.redacted_ids.append(chunk_id)


class FakeVectorDBClient:
    def __init__(self) -> None:
        self.deleted_chunk_ids: list[uuid.UUID] = []

    async def delete_chunk_embedding(self, chunk_id: uuid.UUID) -> None:
        self.deleted_chunk_ids.append(chunk_id)


class FakeGraphClient:
    def __init__(self) -> None:
        self.deleted_chunk_ids: list[uuid.UUID] = []

    async def delete_chunk_node(self, chunk_id: uuid.UUID) -> None:
        self.deleted_chunk_ids.append(chunk_id)


async def test_purge_expired_chunks_deletes_from_all_three_stores() -> None:
    chunk = _chunk()
    chunks_repo = FakeConversationChunkRepository([chunk])
    vectordb = FakeVectorDBClient()
    graph = FakeGraphClient()
    service = RetentionPurgeService(chunks_repo, vectordb, graph)  # type: ignore[arg-type]

    purged_count = await service.purge_expired_chunks()

    assert purged_count == 1
    assert vectordb.deleted_chunk_ids == [chunk.id]
    assert graph.deleted_chunk_ids == [chunk.id]
    assert chunks_repo.redacted_ids == [chunk.id]


async def test_purge_expired_chunks_skips_qdrant_and_neo4j_when_never_linked() -> None:
    """embedding_id/graph_node_ref가 애초에 없던 청크(지식화 파이프라인 미실행)는
    외부 저장소 호출 자체를 건너뛴다 — 존재하지 않는 포인터로 삭제 요청을 보내지 않는다."""
    chunk = _chunk(embedding_id=None, graph_node_ref=None)
    chunks_repo = FakeConversationChunkRepository([chunk])
    vectordb = FakeVectorDBClient()
    graph = FakeGraphClient()
    service = RetentionPurgeService(chunks_repo, vectordb, graph)  # type: ignore[arg-type]

    await service.purge_expired_chunks()

    assert vectordb.deleted_chunk_ids == []
    assert graph.deleted_chunk_ids == []
    assert chunks_repo.redacted_ids == [chunk.id]


async def test_purge_expired_chunks_returns_zero_when_nothing_expired() -> None:
    chunks_repo = FakeConversationChunkRepository([])
    service = RetentionPurgeService(
        chunks_repo,  # type: ignore[arg-type]
        FakeVectorDBClient(),  # type: ignore[arg-type]
        FakeGraphClient(),  # type: ignore[arg-type]
    )

    assert await service.purge_expired_chunks() == 0


async def test_purge_expired_chunks_respects_batch_size() -> None:
    chunks = [_chunk() for _ in range(5)]
    chunks_repo = FakeConversationChunkRepository(chunks)
    service = RetentionPurgeService(
        chunks_repo,  # type: ignore[arg-type]
        FakeVectorDBClient(),  # type: ignore[arg-type]
        FakeGraphClient(),  # type: ignore[arg-type]
    )

    purged_count = await service.purge_expired_chunks(batch_size=2)

    assert purged_count == 2
    assert len(chunks_repo.redacted_ids) == 2
