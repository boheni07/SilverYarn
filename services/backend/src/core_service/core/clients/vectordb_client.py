"""Qdrant 벡터 DB 클라이언트 — decisions.md #28(Qdrant self-hosted 확정), design.md §2.4.

erd.md §1: `embedding_id`는 진짜 FK가 아니라 이 클라이언트가 만든 포인터 문자열이다
(여기서는 Qdrant point id = conversation_chunks.id를 그대로 재사용해 조회를 단순화).
"""

from typing import Any
from uuid import UUID

from qdrant_client import AsyncQdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointIdsList,
    PointStruct,
    VectorParams,
)

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
            # ⚠️ qdrant-client는 `https`를 명시하지 않으면 `api_key is not None`으로
            # https 여부를 추론한다(AsyncQdrantRemote.__init__). `.env.local`의
            # `VECTORDB_API_KEY=`(빈 문자열)가 그대로 들어가면 "키는 있는데 빈 값"이
            # 되어 로컬 평문 HTTP Qdrant에 https로 접속을 시도해 SSL 에러가 난다
            # (decisions.md #56 Q5 실 인프라 검증 중 발견) — 빈 문자열은 None으로
            # 정규화해 로컬/미인증 환경에서 http를 쓰도록 한다.
            api_key=settings.vectordb_api_key or None,
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

    async def delete_chunk_embedding(self, chunk_id: UUID) -> None:
        """decisions.md #56(Q5) — 보유기간 만료된 대화 청크 1건의 벡터 삭제.
        컬렉션이 아직 없으면(한 번도 업서트된 적 없음) 조용히 넘어간다."""
        await self._delete_ignoring_missing_collection(points_selector=PointIdsList(points=[str(chunk_id)]))

    async def delete_user_vectors(self, user_id: UUID) -> None:
        """decisions.md #56(Q5) — 어르신 계정 전체 삭제(erasure) 시, payload.user_id로
        이 사용자의 모든 포인트를 필터 삭제한다(upsert_chunk_embedding이 넣어둔
        {"user_id": str(user_id)} payload 기준)."""
        await self._delete_ignoring_missing_collection(
            points_selector=Filter(must=[FieldCondition(key="user_id", match=MatchValue(value=str(user_id)))])
        )

    async def _delete_ignoring_missing_collection(self, points_selector: Any) -> None:
        try:
            await self._client.delete(
                collection_name=COLLECTION_CONVERSATION_CHUNKS, points_selector=points_selector
            )
        except (UnexpectedResponse, ValueError) as exc:
            # 컬렉션 자체가 없으면(아직 한 번도 청크가 업서트된 적 없는 이 사용자)
            # "지울 게 없다"는 뜻이라 정상 종료로 취급한다.
            message = str(exc).lower()
            if "not found" not in message and "doesn't exist" not in message:
                raise

    async def close(self) -> None:
        await self._client.close()
