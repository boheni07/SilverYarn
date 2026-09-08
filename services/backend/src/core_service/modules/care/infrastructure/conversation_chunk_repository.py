"""conversation_chunks 테이블 SQLAlchemy 매핑 + Repository — schema.md §5 DDL과 1:1.

Append-Only 엔티티다(sync-contract.md §3 — 충돌정책 표에서도 "충돌 없음"으로 분류).
원본 구술 필드(transcript_*, meta_*)는 절대 갱신하지 않는다 — 유일한 예외는
`attach_knowledge_refs()`로, 지식화 파이프라인이 만든 외부 시스템 포인터
(embedding_id/graph_node_ref) 2개만 최초 1회 채운다.
"""

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import ARRAY, DateTime, ForeignKey, Integer, String, Text, select
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from core_service.core.db import Base
from core_service.modules.care.domain.conversation_chunk import ConversationChunk, ConversationMode


class ConversationChunkModel(Base):
    __tablename__ = "conversation_chunks"

    id: Mapped[uuid.UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    raw_audio_ref: Mapped[str] = mapped_column(String(500), nullable=False)
    transcript_on_device: Mapped[str] = mapped_column(Text, nullable=False)
    transcript_server: Mapped[str | None] = mapped_column(Text, nullable=True)
    meta_period: Mapped[str | None] = mapped_column(String(20), nullable=True)
    meta_people: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    meta_place: Mapped[str | None] = mapped_column(String(100), nullable=True)
    meta_emotion: Mapped[str | None] = mapped_column(String(50), nullable=True)
    meta_prosody: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    linked_photo_id: Mapped[uuid.UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("photos.id"), nullable=True
    )
    embedding_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    graph_node_ref: Mapped[str | None] = mapped_column(String(100), nullable=True)
    session_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    turn_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mode: Mapped[str | None] = mapped_column(
        SAEnum("author", "care", "assist", name="conversation_mode", create_type=False),
        nullable=True,
    )
    assistant_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    def to_domain(self) -> ConversationChunk:
        return ConversationChunk(
            id=self.id,
            user_id=self.user_id,
            raw_audio_ref=self.raw_audio_ref,
            transcript_on_device=self.transcript_on_device,
            transcript_server=self.transcript_server,
            meta_period=self.meta_period,
            meta_people=self.meta_people,
            meta_place=self.meta_place,
            meta_emotion=self.meta_emotion,
            meta_prosody=self.meta_prosody,
            linked_photo_id=self.linked_photo_id,
            embedding_id=self.embedding_id,
            graph_node_ref=self.graph_node_ref,
            session_id=self.session_id,
            turn_id=self.turn_id,
            mode=ConversationMode(self.mode) if self.mode else None,
            assistant_response=self.assistant_response,
            created_at=self.created_at,
        )


class ConversationChunkRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, chunk_id: uuid.UUID) -> ConversationChunk | None:
        model = await self._session.get(ConversationChunkModel, chunk_id)
        return model.to_domain() if model else None

    async def list_by_user(
        self, user_id: uuid.UUID, limit: int = 50, offset: int = 0
    ) -> list[ConversationChunk]:
        result = await self._session.execute(
            select(ConversationChunkModel)
            .where(ConversationChunkModel.user_id == user_id)
            .order_by(ConversationChunkModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return [m.to_domain() for m in result.scalars().all()]

    async def search_by_keyword(self, user_id: uuid.UUID, keyword: str) -> list[ConversationChunk]:
        """TODO(다음 스프린트): 이건 임시 ILIKE 검색이다. 실제로는 design.md §2.4 RAG
        파이프라인(Qdrant BM25+Dense 하이브리드, decisions.md #28)을 rag-core 모듈이
        구현한 뒤 그쪽으로 위임해야 한다 — 온디바이스 FTS5(#32)와 달리 서버는 하이브리드
        서치가 확정 스펙이므로, 이 메서드를 그대로 프로덕션에 쓰면 안 된다.
        """
        pattern = f"%{keyword}%"
        result = await self._session.execute(
            select(ConversationChunkModel)
            .where(
                ConversationChunkModel.user_id == user_id,
                ConversationChunkModel.transcript_server.ilike(pattern),
            )
            .order_by(ConversationChunkModel.created_at.desc())
        )
        return [m.to_domain() for m in result.scalars().all()]

    async def create(
        self,
        user_id: uuid.UUID,
        raw_audio_ref: str,
        transcript_on_device: str,
        mode: ConversationMode | None,
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
        """workflow-diagrams.md §2/§3 — 온디바이스 발화 업로드 시 서버가 적재.

        Append-Only라 upsert가 아니라 항상 신규 insert다. embedding_id/graph_node_ref는
        지식화 파이프라인(§3)이 나중에 채운다 — 이 메서드는 그 이전 단계 값만 받는다.
        """
        model = ConversationChunkModel(
            id=uuid.uuid4(),
            user_id=user_id,
            raw_audio_ref=raw_audio_ref,
            transcript_on_device=transcript_on_device,
            transcript_server=transcript_server,
            meta_period=meta_period,
            meta_people=meta_people,
            meta_place=meta_place,
            meta_emotion=meta_emotion,
            meta_prosody=meta_prosody,
            linked_photo_id=linked_photo_id,
            embedding_id=None,
            graph_node_ref=None,
            session_id=session_id,
            turn_id=turn_id,
            mode=mode.value if mode else None,
            assistant_response=assistant_response,
            created_at=datetime.now(UTC),
        )
        self._session.add(model)
        await self._session.flush()
        return model.to_domain()

    async def attach_knowledge_refs(
        self, chunk_id: uuid.UUID, embedding_id: str | None, graph_node_ref: str | None
    ) -> ConversationChunk:
        """지식화 파이프라인(§3)이 Qdrant/Neo4j 적재 후 포인터를 채워 넣는다.

        Append-Only 원칙(모듈 상단 docstring)에 대한 유일한 예외 — 원본 구술 내용은
        절대 바꾸지 않고, 외부 시스템 포인터 2개만 최초 1회 채운다.
        """
        model = await self._session.get(ConversationChunkModel, chunk_id)
        if model is None:
            raise LookupError(f"conversation_chunk {chunk_id} not found")
        model.embedding_id = embedding_id
        model.graph_node_ref = graph_node_ref
        await self._session.flush()
        return model.to_domain()
