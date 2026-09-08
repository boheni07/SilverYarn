"""Qdrant 벡터 DB 클라이언트 — decisions.md #28(Qdrant self-hosted 확정), design.md §2.4.

erd.md §1: `embedding_id`는 진짜 FK가 아니라 이 클라이언트가 만든 포인터 문자열이다
(여기서는 Qdrant point id = conversation_chunks.id를 그대로 재사용해 조회를 단순화).
"""

from typing import Any
from uuid import UUID

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from core_service.core.config import get_settings

# BGE-M3 임베딩 차원 — 모델 확정(decisions.md)에 따른 표준값. 실제 배포 모델이
# 다르면 이 값과 컬렉션을 함께 재생성해야 한다.
BGE_M3_VECTOR_SIZE = 1024
COLLECTION_CONVERSATION_CHUNKS = "conversation_chunks"


class VectorDBClient:
    def __init__(self) -> None:
        settings = get_settings()
        self._client = AsyncQdrantClient(
            host=settings.vectordb_host,
            port=settings.vectordb_port,
            api_key=settings.vectordb_api_key,
        )

    async def _ensure_collection(self, name: str, vector_size: int) -> None:
        existing = await self._client.get_collections()
        if name not in [c.name for c in existing.collections]:
            await self._client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )

    async def upsert_chunk_embedding(
        self, chunk_id: UUID, vector: list[float], payload: dict[str, Any]
    ) -> str:
        """conversation_chunks 청크 1건의 임베딩을 적재하고 embedding_id(포인터)를 반환."""
        await self._ensure_collection(COLLECTION_CONVERSATION_CHUNKS, len(vector))
        await self._client.upsert(
            collection_name=COLLECTION_CONVERSATION_CHUNKS,
            points=[PointStruct(id=str(chunk_id), vector=vector, payload=payload)],
        )
        return str(chunk_id)

    async def close(self) -> None:
        await self._client.close()
