"""ConversationChunk 유스케이스 — workflow-diagrams.md §2(온디바이스 파이프라인)·
§3(배치 동기화)의 서버측 적재 지점.

`record_chunk()`는 author 모듈의 `save_draft()`와 같은 성격이다: sync 모듈의
UploadPipelineService가 호출하며 공개 POST 엔드포인트로 노출하지 않는다 — 대화
청크는 클라이언트가 임의로 만드는 리소스가 아니라 업로드 파이프라인의 산출물이기
때문이다.
"""

import uuid
from datetime import datetime
from typing import Any

from core_service.core.errors import ApiError
from core_service.modules.care.domain.conversation_chunk import ConversationChunk, ConversationMode
from core_service.modules.care.infrastructure.conversation_chunk_repository import (
    ConversationChunkRepository,
)


class ConversationChunkService:
    def __init__(self, repo: ConversationChunkRepository):
        self._repo = repo

    async def get_chunk(self, chunk_id: uuid.UUID) -> ConversationChunk:
        chunk = await self._repo.get_by_id(chunk_id)
        if chunk is None:
            raise ApiError("NOT_FOUND", f"대화 청크({chunk_id})를 찾을 수 없습니다.")
        return chunk

    async def find_existing_turn(
        self, user_id: uuid.UUID, session_id: str, turn_id: int
    ) -> ConversationChunk | None:
        """업로드 파이프라인이 재처리 전에 "이미 적재된 턴인지" 확인하는 용도
        (sync-contract.md §2 멱등성). 모듈 경계상 UploadPipelineService가 repo를
        직접 만지지 않도록 서비스에 노출한다."""
        return await self._repo.find_by_turn(user_id, session_id, turn_id)

    async def list_chunks_for_user(
        self, user_id: uuid.UUID, limit: int = 50, offset: int = 0
    ) -> list[ConversationChunk]:
        if limit < 1 or limit > 200:
            raise ApiError("VALIDATION_ERROR", "limit은 1~200 사이여야 합니다.")
        return await self._repo.list_by_user(user_id, limit=limit, offset=offset)

    async def count_chunks_since(self, user_id: uuid.UUID, since: datetime) -> int:
        return await self._repo.count_since(user_id, since)

    async def search_chunks(self, user_id: uuid.UUID, keyword: str) -> list[ConversationChunk]:
        if not keyword:
            raise ApiError("VALIDATION_ERROR", "keyword는 비어 있을 수 없습니다.")
        return await self._repo.search_by_keyword(user_id, keyword)

    async def record_chunk(
        self,
        user_id: uuid.UUID,
        raw_audio_ref: str,
        transcript_on_device: str,
        mode: ConversationMode | None = None,
        session_id: str | None = None,
        turn_id: int | None = None,
        transcript_server: str | None = None,
        meta_period: str | None = None,
        meta_people: list[str] | None = None,
        meta_place: str | None = None,
        meta_emotion: str | None = None,
        meta_prosody: dict[str, Any] | None = None,
        linked_photo_id: uuid.UUID | None = None,
        assistant_response: str | None = None,
    ) -> ConversationChunk:
        if not raw_audio_ref:
            raise ApiError("VALIDATION_ERROR", "raw_audio_ref는 비어 있을 수 없습니다.")
        if not transcript_on_device:
            raise ApiError("VALIDATION_ERROR", "transcript_on_device는 비어 있을 수 없습니다.")
        return await self._repo.create(
            user_id=user_id,
            raw_audio_ref=raw_audio_ref,
            transcript_on_device=transcript_on_device,
            mode=mode,
            session_id=session_id,
            turn_id=turn_id,
            transcript_server=transcript_server,
            meta_period=meta_period,
            meta_people=meta_people,
            meta_place=meta_place,
            meta_emotion=meta_emotion,
            meta_prosody=meta_prosody,
            linked_photo_id=linked_photo_id,
            assistant_response=assistant_response,
        )

    async def attach_knowledge_refs(
        self, chunk_id: uuid.UUID, embedding_id: str | None, graph_node_ref: str | None
    ) -> ConversationChunk:
        """UploadPipelineService가 Qdrant/Neo4j 적재 성공 후 호출 — 둘 다 None이면
        아무 의미 없는 호출이지만 막지 않는다(파이프라인이 두 단계 다 실패해도
        청크 자체는 이미 존재해야 하므로, 이 메서드를 항상 호출해도 안전하게)."""
        return await self._repo.attach_knowledge_refs(chunk_id, embedding_id, graph_node_ref)
