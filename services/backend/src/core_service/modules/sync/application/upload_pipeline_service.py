"""업로드 파이프라인 오케스트레이션 — workflow-diagrams.md §3(배치 동기화)·
§4(작가 엔진 상세 흐름)의 서버측 실행 로직. worker.py의 `process_upload` 잡이
이 서비스 하나만 호출한다.

**Best-effort 원칙**: STT 재전사·지식추출(LLM)·임베딩(Qdrant)·그래프 적재(Neo4j)는
전부 아직 존재하지 않는 온프레미스 인프라를 향한 호출이다. 이 서비스는 각 단계를
개별적으로 try/except로 감싸 실패해도 다음 단계로 진행한다 — 최소한 온디바이스
전사 그대로 `conversation_chunks`에는 적재되도록 보장한다. `conversation_chunks`
적재 자체(DB 쓰기)가 실패하면 예외를 그대로 던진다.

**sync_sessions 상태 갱신은 이 서비스의 책임이 아니다**: 실제 DB로 엔드투엔드
테스트하다가, 청크 적재 flush 실패로 세션이 "poisoned"(SQLAlchemy 용어로
PendingRollbackError 상태)된 뒤 같은 세션으로 `sync_sessions.status=failed`를
쓰려다 2차 예외가 나 원래 오류를 가려버리는 문제를 발견했다. 해결책은 상태
갱신을 **별도의 독립 세션/트랜잭션**으로 분리하는 것 — 그 책임은 worker.py가
진다(worker.py의 `_update_sync_status` 참조). 이 서비스는 파이프라인 실행에만
집중하고 성공/실패 여부는 예외 유무로만 알린다.
"""

import logging
import uuid
from dataclasses import dataclass

from core_service.core.clients.embedding_client import EmbeddingClient
from core_service.core.clients.graph_client import GraphClient
from core_service.core.clients.llm_client import LLMClient
from core_service.core.clients.stt_client import STTClient
from core_service.core.clients.vectordb_client import VectorDBClient
from core_service.modules.author.application.chapter_service import ChapterService
from core_service.modules.author.domain.chapter import ChapterPeriod
from core_service.modules.care.application.conversation_chunk_service import (
    ConversationChunkService,
)
from core_service.modules.care.domain.conversation_chunk import ConversationChunk, ConversationMode

logger = logging.getLogger(__name__)

# TODO(Do 단계 재설계 필요): 인생 시기 4개 고정 매핑 — 챕터 자동 귀속(workflow-diagrams.md
# §4 "챕터 자동 귀속" 단계)의 최소 구현. 실제로는 같은 시기 내 다중 챕터 분화가 필요하다.
PERIOD_TO_CHAPTER_NO: dict[ChapterPeriod, int] = {
    ChapterPeriod.CHILDHOOD: 1,
    ChapterPeriod.YOUTH: 2,
    ChapterPeriod.ADULTHOOD: 3,
    ChapterPeriod.PRESENT: 4,
}

# schema.md §7 한글 표시명 매핑 — 챕터 제목 자동 생성용 최소 구현.
PERIOD_DISPLAY_NAME: dict[ChapterPeriod, str] = {
    ChapterPeriod.CHILDHOOD: "유년기",
    ChapterPeriod.YOUTH: "청년기",
    ChapterPeriod.ADULTHOOD: "중장년기",
    ChapterPeriod.PRESENT: "현재",
}


@dataclass
class UploadPipelineInput:
    """arq 잡 인자를 한데 묶은 값 객체 — worker.py가 이 형태로 조립해 넘긴다."""

    sync_session_id: uuid.UUID
    user_id: uuid.UUID
    raw_audio_ref: str
    transcript_on_device: str
    mode: ConversationMode | None = None
    device_session_id: str | None = None
    turn_id: int | None = None


class UploadPipelineService:
    def __init__(
        self,
        chunk_service: ConversationChunkService,
        chapter_service: ChapterService,
        stt_client: STTClient,
        embedding_client: EmbeddingClient,
        llm_client: LLMClient,
        vectordb_client: VectorDBClient,
        graph_client: GraphClient,
    ):
        self._chunks = chunk_service
        self._chapters = chapter_service
        self._stt = stt_client
        self._embedding = embedding_client
        self._llm = llm_client
        self._vectordb = vectordb_client
        self._graph = graph_client

    async def run(self, data: UploadPipelineInput) -> ConversationChunk:
        """전체 파이프라인 1회 실행. `conversation_chunks` 적재 자체가 실패하면
        예외를 그대로 던진다 — 세션/트랜잭션 처리는 호출자(worker.py) 책임이다.

        멱등성(sync-contract.md §2): 같은 `(user_id, session_id, turn_id)`가 이미
        적재됐으면 재처리하지 않고 기존 청크를 그대로 돌려준다 — 재전송/잡 재시도로
        STT·임베딩·**챕터 윤문(save_draft가 version을 올리며 본문을 덧붙임)**이 중복
        실행되는 것을 막는다.
        """
        if data.device_session_id is not None and data.turn_id is not None:
            existing = await self._chunks.find_existing_turn(
                data.user_id, data.device_session_id, data.turn_id
            )
            if existing is not None:
                logger.info(
                    "이미 처리된 턴 — 파이프라인 건너뜀. session=%s turn=%s",
                    data.device_session_id,
                    data.turn_id,
                )
                return existing

        transcript_server = await self._safe_transcribe(data.raw_audio_ref, data.transcript_on_device)
        knowledge = await self._safe_extract_knowledge(transcript_server)

        chunk = await self._chunks.record_chunk(
            user_id=data.user_id,
            raw_audio_ref=data.raw_audio_ref,
            transcript_on_device=data.transcript_on_device,
            transcript_server=transcript_server,
            mode=data.mode,
            session_id=data.device_session_id,
            turn_id=data.turn_id,
            meta_period=knowledge.get("period"),
            meta_people=knowledge.get("people"),
            meta_place=knowledge.get("place"),
            meta_emotion=knowledge.get("emotion"),
        )

        embedding_id = await self._safe_embed_and_upsert(chunk, transcript_server)
        graph_node_ref = await self._safe_upsert_graph(chunk, knowledge)
        if embedding_id or graph_node_ref:
            await self._chunks.attach_knowledge_refs(chunk.id, embedding_id, graph_node_ref)

        transcript_for_chapter = transcript_server or data.transcript_on_device
        await self._safe_update_chapter(data.user_id, knowledge, transcript_for_chapter)

        return chunk

    # --- best-effort 단계들: 실패해도 파이프라인을 막지 않는다 ---

    async def _safe_transcribe(self, raw_audio_ref: str, fallback: str) -> str:
        try:
            return await self._stt.transcribe(raw_audio_ref)
        except Exception:
            logger.warning("STT 재전사 실패 — 온디바이스 전사로 대체. raw_audio_ref=%s", raw_audio_ref)
            return fallback

    async def _safe_extract_knowledge(self, transcript: str) -> dict:
        try:
            return await self._llm.extract_knowledge(transcript)
        except Exception:
            logger.warning("지식 추출 실패 — 메타데이터 없이 진행")
            return {}

    async def _safe_embed_and_upsert(self, chunk: ConversationChunk, transcript: str | None) -> str | None:
        text = transcript or chunk.transcript_on_device
        try:
            vector = await self._embedding.embed(text)
            return await self._vectordb.upsert_chunk_embedding(
                chunk.id, vector, payload={"user_id": str(chunk.user_id)}
            )
        except Exception:
            logger.warning("임베딩 적재 실패 — chunk_id=%s", chunk.id)
            return None

    async def _safe_upsert_graph(self, chunk: ConversationChunk, knowledge: dict) -> str | None:
        try:
            return await self._graph.upsert_chunk_node(
                chunk_id=chunk.id,
                user_id=chunk.user_id,
                people=knowledge.get("people"),
                place=knowledge.get("place"),
                period=knowledge.get("period"),
            )
        except Exception:
            logger.warning("그래프 적재 실패 — chunk_id=%s", chunk.id)
            return None

    async def _safe_update_chapter(self, user_id: uuid.UUID, knowledge: dict, transcript: str) -> None:
        period_value = knowledge.get("period")
        if not period_value:
            return  # 시기를 특정 못하면 챕터 귀속을 시도하지 않는다(추측 금지)
        try:
            period = ChapterPeriod(period_value)
        except ValueError:
            logger.warning("알 수 없는 period 값 — 챕터 귀속 건너뜀: %s", period_value)
            return

        chapter_no = PERIOD_TO_CHAPTER_NO[period]
        existing = await self._chapters.get_chapter_by_user_and_no(user_id, chapter_no)
        existing_body = existing.body_text if existing else None

        try:
            body_text = await self._llm.generate_chapter_draft(existing_body, transcript)
        except Exception:
            logger.warning("챕터 윤문 실패 — 단순 이어붙이기로 대체")
            body_text = f"{existing_body}\n\n{transcript}" if existing_body else transcript

        title = existing.title if existing else f"{PERIOD_DISPLAY_NAME[period]} 기록"
        try:
            chapter = await self._chapters.save_draft(
                user_id=user_id,
                chapter_no=chapter_no,
                title=title,
                period=period,
                body_text=body_text,
            )
        except Exception:
            logger.exception("챕터 초안 저장 실패 — user_id=%s, chapter_no=%s", user_id, chapter_no)
            return

        await self._safe_compact_chapter(chapter.id)

    async def _safe_compact_chapter(self, chapter_id: uuid.UUID) -> None:
        """design §2.11 4단계 — 저장된 챕터를 온디바이스 FTS5용 요약·키워드로 압축.
        vLLM 미가동/파싱 실패 시 이전 요약(또는 없음)을 유지하고 파이프라인은 계속한다 —
        `GET /sync/download`가 요약이 없으면 body_text를 잘라서 임시로 내려보낸다."""
        try:
            await self._chapters.compact_chapter(chapter_id, self._llm)
        except Exception:
            logger.warning("챕터 Compaction 실패 — 이전 요약 유지. chapter_id=%s", chapter_id)
