"""conversation_chunks 테이블 SQLAlchemy 매핑 + Repository — schema.md §5 DDL과 1:1.

Append-Only 엔티티다(sync-contract.md §3 — 충돌정책 표에서도 "충돌 없음"으로 분류).
원본 구술 필드(transcript_*, meta_*)는 절대 갱신하지 않는다 — 유일한 예외는
`attach_knowledge_refs()`로, 지식화 파이프라인이 만든 외부 시스템 포인터
(embedding_id/graph_node_ref) 2개만 최초 1회 채운다.

PII 암호화 대상(schema.md §5, decisions.md #45): `transcript_on_device`,
`transcript_server`, `assistant_response`. 사용자별 DEK로 이 계층에서 투명하게
암복호화한다(core/crypto.py). `meta_*`는 이번 라운드 대상이 아니다.
"""

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import ARRAY, DateTime, ForeignKey, Integer, String, Text, func, select
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from core_service.core.crypto import PiiFieldEncryptor, get_pii_encryptor
from core_service.core.db import Base
from core_service.modules.care.domain.conversation_chunk import ConversationChunk, ConversationMode


class ConversationChunkModel(Base):
    __tablename__ = "conversation_chunks"

    id: Mapped[uuid.UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    raw_audio_ref: Mapped[str] = mapped_column(String(500), nullable=False)
    transcript_on_device: Mapped[str] = mapped_column(Text, nullable=False)  # 저장 시 암호문
    transcript_server: Mapped[str | None] = mapped_column(Text, nullable=True)  # 저장 시 암호문
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
    assistant_response: Mapped[str | None] = mapped_column(Text, nullable=True)  # 저장 시 암호문
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ConversationChunkRepository:
    def __init__(self, session: AsyncSession, pii: PiiFieldEncryptor | None = None):
        self._session = session
        self._pii = pii or get_pii_encryptor()

    async def _to_domain(self, model: ConversationChunkModel) -> ConversationChunk:
        return ConversationChunk(
            id=model.id,
            user_id=model.user_id,
            raw_audio_ref=model.raw_audio_ref,
            transcript_on_device=await self._pii.decrypt(
                self._session, model.user_id, model.transcript_on_device
            ),
            transcript_server=await self._pii.decrypt_opt(
                self._session, model.user_id, model.transcript_server
            ),
            meta_period=model.meta_period,
            meta_people=model.meta_people,
            meta_place=model.meta_place,
            meta_emotion=model.meta_emotion,
            meta_prosody=model.meta_prosody,
            linked_photo_id=model.linked_photo_id,
            embedding_id=model.embedding_id,
            graph_node_ref=model.graph_node_ref,
            session_id=model.session_id,
            turn_id=model.turn_id,
            mode=ConversationMode(model.mode) if model.mode else None,
            assistant_response=await self._pii.decrypt_opt(
                self._session, model.user_id, model.assistant_response
            ),
            created_at=model.created_at,
        )

    async def get_by_id(self, chunk_id: uuid.UUID) -> ConversationChunk | None:
        model = await self._session.get(ConversationChunkModel, chunk_id)
        return await self._to_domain(model) if model else None

    async def find_by_turn(
        self, user_id: uuid.UUID, session_id: str, turn_id: int
    ) -> ConversationChunk | None:
        """업로드 멱등성(sync-contract.md §2) — 온디바이스 한 턴 = 한 행.
        마이그레이션 0004의 부분 유니크 인덱스 `uq_conversation_chunks_turn`와 짝을 이룬다."""
        result = await self._session.execute(
            select(ConversationChunkModel).where(
                ConversationChunkModel.user_id == user_id,
                ConversationChunkModel.session_id == session_id,
                ConversationChunkModel.turn_id == turn_id,
            )
        )
        model = result.scalar_one_or_none()
        return await self._to_domain(model) if model else None

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
        return [await self._to_domain(m) for m in result.scalars().all()]

    async def count_since(self, user_id: uuid.UUID, since: datetime) -> int:
        """가족 대시보드(WF1) "오늘 대화" 통계용 — transcript_*를 복호화하지 않고
        COUNT(*)만 셈한다(불필요한 PII 노출 회피)."""
        result = await self._session.execute(
            select(func.count())
            .select_from(ConversationChunkModel)
            .where(
                ConversationChunkModel.user_id == user_id,
                ConversationChunkModel.created_at >= since,
            )
        )
        return result.scalar_one()

    async def search_by_keyword(self, user_id: uuid.UUID, keyword: str) -> list[ConversationChunk]:
        """TODO(다음 스프린트): 이건 임시 검색이다. 실제로는 design.md §2.4 RAG
        파이프라인(Qdrant BM25+Dense 하이브리드, decisions.md #28)을 rag-core 모듈이
        구현한 뒤 그쪽으로 위임해야 한다 — 온디바이스 FTS5(#32)와 달리 서버는 하이브리드
        서치가 확정 스펙이므로, 이 메서드를 그대로 프로덕션에 쓰면 안 된다.

        ⚠️ transcript_*가 암호화(decisions.md #45)된 뒤로는 SQL ILIKE가 불가능하다 —
        사용자 청크를 전부 복호화해 파이썬에서 부분일치를 거른다. 임시 메서드라
        감수하지만, 사용자별 청크 수가 커지면 그 자체로 못 쓰게 되는 접근이다.
        """
        result = await self._session.execute(
            select(ConversationChunkModel)
            .where(ConversationChunkModel.user_id == user_id)
            .order_by(ConversationChunkModel.created_at.desc())
        )
        chunks = [await self._to_domain(m) for m in result.scalars().all()]
        return [c for c in chunks if c.transcript_server and keyword in c.transcript_server]

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

        멱등성: `(user_id, session_id, turn_id)`가 중복되면(동시 실행되던 다른 잡이
        먼저 INSERT) `uq_conversation_chunks_turn`(마이그레이션 0004)이 IntegrityError를
        던진다 — 그 경우 이미 있는 행을 돌려준다. 파이프라인은 이 중복을 사전에도
        `find_by_turn`으로 거르지만(upload_pipeline_service), 경쟁 상황의 안전망이다.
        """
        if session_id is not None and turn_id is not None:
            existing = await self.find_by_turn(user_id, session_id, turn_id)
            if existing is not None:
                return existing

        model = ConversationChunkModel(
            id=uuid.uuid4(),
            user_id=user_id,
            raw_audio_ref=raw_audio_ref,
            transcript_on_device=await self._pii.encrypt(self._session, user_id, transcript_on_device),
            transcript_server=await self._pii.encrypt_opt(self._session, user_id, transcript_server),
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
            assistant_response=await self._pii.encrypt_opt(self._session, user_id, assistant_response),
            created_at=datetime.now(UTC),
        )
        self._session.add(model)
        try:
            async with self._session.begin_nested():
                await self._session.flush()
        except IntegrityError:
            if session_id is not None and turn_id is not None:
                existing = await self.find_by_turn(user_id, session_id, turn_id)
                if existing is not None:
                    return existing
            raise
        return await self._to_domain(model)

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
        return await self._to_domain(model)
