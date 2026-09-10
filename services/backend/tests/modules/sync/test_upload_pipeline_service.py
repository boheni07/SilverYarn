"""UploadPipelineService 유닛 테스트 — 페이크 Repository/클라이언트로 DB·외부
인프라 없이 오케스트레이션 로직을 검증한다.

care/author의 실제 Service 클래스는 그대로 쓰고(Application 계층 로직까지 함께
검증), Repository와 외부 클라이언트(STT/LLM/Embedding/Qdrant/Neo4j)만 페이크로
대체한다 — 이 페이크들이 곧 "실제 인프라가 준비됐을 때 이 인터페이스를 만족해야
한다"는 계약 문서 역할도 한다.

⚠️ sync_sessions 상태 갱신(SUCCESS/FAILED)은 이 서비스의 책임이 아니다(worker.py가
별도 세션으로 처리 — 실제 DB로 엔드투엔드 테스트하다 발견한 세션 오염 문제 때문,
worker.py 상단 docstring 참조). 그래서 이 테스트는 `run()`의 반환값/예외 여부만
검증하고 sync_sessions 상태는 다루지 않는다.
"""

import uuid
from datetime import UTC, datetime

import pytest

from core_service.modules.author.application.chapter_service import ChapterService
from core_service.modules.author.domain.chapter import Chapter, ChapterCompaction, ChapterStatus
from core_service.modules.care.application.conversation_chunk_service import (
    ConversationChunkService,
)
from core_service.modules.care.domain.conversation_chunk import ConversationChunk, ConversationMode
from core_service.modules.sync.application.upload_pipeline_service import (
    UploadPipelineInput,
    UploadPipelineService,
)

# --- 페이크 Repository (author/care 테스트 파일과 같은 패턴, 이 파일에 독립 정의) ---


class FakeChapterRepository:
    def __init__(self) -> None:
        self.by_id: dict[uuid.UUID, Chapter] = {}

    async def get_by_id(self, chapter_id):
        return self.by_id.get(chapter_id)

    async def list_by_user(self, user_id):
        return [c for c in self.by_id.values() if c.user_id == user_id]

    async def get_by_user_and_no(self, user_id, chapter_no):
        return next(
            (c for c in self.by_id.values() if c.user_id == user_id and c.chapter_no == chapter_no),
            None,
        )

    async def upsert_draft(self, user_id, chapter_no, title, period, body_text):
        existing = await self.get_by_user_and_no(user_id, chapter_no)
        if existing:
            existing.title = title
            existing.period = period
            existing.body_text = body_text
            existing.version += 1
            return existing
        chapter = Chapter(
            id=uuid.uuid4(),
            user_id=user_id,
            chapter_no=chapter_no,
            title=title,
            period=period,
            body_text=body_text,
            status=ChapterStatus.DRAFT,
            version=1,
            updated_at=datetime.now(UTC),
        )
        self.by_id[chapter.id] = chapter
        return chapter

    async def update_status(self, chapter_id, status, bump_version=False):
        chapter = self.by_id[chapter_id]
        chapter.status = status
        return chapter

    async def set_compaction(self, chapter_id, *, summary, keywords, source_version):
        chapter = self.by_id[chapter_id]
        chapter.compaction = ChapterCompaction(
            summary=summary, keywords=list(keywords), source_version=source_version
        )


class FakeChapterRevisionRepository:
    async def list_by_chapter(self, chapter_id):
        return []

    async def create(self, **kwargs):
        raise AssertionError("파이프라인은 chapter_revisions를 생성하면 안 된다(M-5)")


class FakeConversationChunkRepository:
    def __init__(self, fail_create: bool = False) -> None:
        self._store: dict[uuid.UUID, ConversationChunk] = {}
        self._fail_create = fail_create

    async def get_by_id(self, chunk_id):
        return self._store.get(chunk_id)

    async def find_by_turn(self, user_id, session_id, turn_id):
        return next(
            (
                c
                for c in self._store.values()
                if c.user_id == user_id and c.session_id == session_id and c.turn_id == turn_id
            ),
            None,
        )

    async def list_by_user(self, user_id, limit=50, offset=0):
        return [c for c in self._store.values() if c.user_id == user_id]

    async def search_by_keyword(self, user_id, keyword):
        return []

    async def create(self, user_id, raw_audio_ref, transcript_on_device, mode, **kwargs):
        if self._fail_create:
            raise RuntimeError("DB 쓰기 실패 시뮬레이션")
        chunk = ConversationChunk(
            id=uuid.uuid4(),
            user_id=user_id,
            raw_audio_ref=raw_audio_ref,
            transcript_on_device=transcript_on_device,
            transcript_server=kwargs.get("transcript_server"),
            meta_period=kwargs.get("meta_period"),
            meta_people=kwargs.get("meta_people"),
            meta_place=kwargs.get("meta_place"),
            meta_emotion=kwargs.get("meta_emotion"),
            meta_prosody=kwargs.get("meta_prosody"),
            linked_photo_id=kwargs.get("linked_photo_id"),
            embedding_id=None,
            graph_node_ref=None,
            session_id=kwargs.get("session_id"),
            turn_id=kwargs.get("turn_id"),
            mode=mode,
            assistant_response=kwargs.get("assistant_response"),
            created_at=datetime.now(UTC),
        )
        self._store[chunk.id] = chunk
        return chunk

    async def attach_knowledge_refs(self, chunk_id, embedding_id, graph_node_ref):
        chunk = self._store[chunk_id]
        chunk.embedding_id = embedding_id
        chunk.graph_node_ref = graph_node_ref
        return chunk


# --- 페이크 외부 클라이언트 ---


class FakeSTTClient:
    def __init__(self, fail: bool = False, text: str = "정밀 재전사 결과"):
        self._fail = fail
        self._text = text

    async def transcribe(self, raw_audio_ref: str) -> str:
        if self._fail:
            raise RuntimeError("STT 서비스 연결 실패")
        return self._text


class FakeLLMClient:
    def __init__(
        self,
        fail_extract: bool = False,
        fail_generate: bool = False,
        fail_compact: bool = False,
        knowledge: dict | None = None,
    ):
        self._fail_extract = fail_extract
        self._fail_generate = fail_generate
        self._fail_compact = fail_compact
        self._knowledge = knowledge if knowledge is not None else {}

    async def extract_knowledge(self, transcript: str) -> dict:
        if self._fail_extract:
            raise RuntimeError("LLM 지식추출 실패")
        return self._knowledge

    async def generate_chapter_draft(self, existing_body, new_transcript) -> str:
        if self._fail_generate:
            raise RuntimeError("LLM 윤문 실패")
        return f"[윤문됨] {new_transcript}"

    async def compact_chapter(self, body_text: str) -> tuple[str, list[str]]:
        if self._fail_compact:
            raise RuntimeError("LLM Compaction 실패")
        return f"[요약] {body_text[:20]}", ["키워드1", "키워드2"]


class FakeEmbeddingClient:
    def __init__(self, fail: bool = False):
        self._fail = fail

    async def embed(self, text: str) -> list[float]:
        if self._fail:
            raise RuntimeError("임베딩 서비스 실패")
        return [0.1, 0.2, 0.3]


class FakeVectorDBClient:
    def __init__(self, fail: bool = False):
        self._fail = fail

    async def upsert_chunk_embedding(self, chunk_id, vector, payload) -> str:
        if self._fail:
            raise RuntimeError("Qdrant 적재 실패")
        return f"qdrant:{chunk_id}"


class FakeGraphClient:
    def __init__(self, fail: bool = False):
        self._fail = fail

    async def upsert_chunk_node(self, chunk_id, user_id, people, place, period) -> str:
        if self._fail:
            raise RuntimeError("Neo4j 적재 실패")
        return f"neo4j:{chunk_id}"


def _build_pipeline(
    *,
    chunk_repo=None,
    chapter_repo=None,
    revision_repo=None,
    stt=None,
    embedding=None,
    llm=None,
    vectordb=None,
    graph=None,
) -> tuple[UploadPipelineService, FakeConversationChunkRepository]:
    chunk_repo = chunk_repo or FakeConversationChunkRepository()
    chapter_repo = chapter_repo or FakeChapterRepository()
    revision_repo = revision_repo or FakeChapterRevisionRepository()
    pipeline = UploadPipelineService(
        chunk_service=ConversationChunkService(chunk_repo),
        chapter_service=ChapterService(chapter_repo, revision_repo),
        stt_client=stt or FakeSTTClient(),
        embedding_client=embedding or FakeEmbeddingClient(),
        llm_client=llm or FakeLLMClient(),
        vectordb_client=vectordb or FakeVectorDBClient(),
        graph_client=graph or FakeGraphClient(),
    )
    return pipeline, chunk_repo


def _input(**overrides) -> UploadPipelineInput:
    defaults = dict(
        sync_session_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        raw_audio_ref="opus/a.opus",
        transcript_on_device="온디바이스 전사",
        mode=ConversationMode.AUTHOR,
    )
    defaults.update(overrides)
    return UploadPipelineInput(**defaults)


async def test_happy_path_returns_chunk_with_attached_refs() -> None:
    llm = FakeLLMClient(knowledge={"period": "youth", "people": ["김반장"], "place": "인천"})
    pipeline, chunk_repo = _build_pipeline(llm=llm)

    chunk = await pipeline.run(_input())

    stored = await chunk_repo.get_by_id(chunk.id)
    assert stored.transcript_server == "정밀 재전사 결과"
    assert stored.embedding_id == f"qdrant:{chunk.id}"
    assert stored.graph_node_ref == f"neo4j:{chunk.id}"
    assert stored.meta_period == "youth"


async def test_stt_failure_falls_back_to_on_device_transcript() -> None:
    pipeline, chunk_repo = _build_pipeline(stt=FakeSTTClient(fail=True))

    chunk = await pipeline.run(_input(transcript_on_device="폴백 전사"))

    stored = await chunk_repo.get_by_id(chunk.id)
    assert stored.transcript_server == "폴백 전사"  # STT 실패는 치명적이지 않다


async def test_knowledge_extraction_failure_still_creates_chunk_without_chapter_update() -> None:
    chapter_repo = FakeChapterRepository()
    pipeline, chunk_repo = _build_pipeline(llm=FakeLLMClient(fail_extract=True), chapter_repo=chapter_repo)

    chunk = await pipeline.run(_input())

    assert await chunk_repo.get_by_id(chunk.id) is not None
    assert chapter_repo.by_id == {}  # period를 못 구했으니 챕터 귀속 자체를 시도 안 함


async def test_embedding_and_graph_failures_do_not_block_chunk_creation() -> None:
    pipeline, chunk_repo = _build_pipeline(
        embedding=FakeEmbeddingClient(fail=True), graph=FakeGraphClient(fail=True)
    )

    chunk = await pipeline.run(_input())

    stored = await chunk_repo.get_by_id(chunk.id)
    assert stored.embedding_id is None
    assert stored.graph_node_ref is None


async def test_chunk_creation_failure_raises() -> None:
    pipeline, _ = _build_pipeline(chunk_repo=FakeConversationChunkRepository(fail_create=True))

    with pytest.raises(RuntimeError):
        await pipeline.run(_input())


async def test_pipeline_compacts_chapter_after_save() -> None:
    """design §2.11 4단계 — 챕터 저장 뒤 Compaction Engine이 요약·키워드를 채운다."""
    chapter_repo = FakeChapterRepository()
    llm = FakeLLMClient(knowledge={"period": "youth"})
    pipeline, _ = _build_pipeline(llm=llm, chapter_repo=chapter_repo)

    await pipeline.run(_input())

    chapter = next(iter(chapter_repo.by_id.values()))
    assert chapter.compaction is not None
    assert chapter.compaction.keywords == ["키워드1", "키워드2"]
    assert chapter.compaction.source_version == chapter.version


async def test_pipeline_compaction_failure_does_not_break_chunk_or_chapter() -> None:
    chapter_repo = FakeChapterRepository()
    llm = FakeLLMClient(knowledge={"period": "youth"}, fail_compact=True)
    pipeline, chunk_repo = _build_pipeline(llm=llm, chapter_repo=chapter_repo)

    chunk = await pipeline.run(_input())

    assert await chunk_repo.get_by_id(chunk.id) is not None
    chapter = next(iter(chapter_repo.by_id.values()))
    assert chapter.compaction is None  # 요약 실패해도 챕터 자체는 저장됨


async def test_chapter_generation_failure_falls_back_to_concatenation() -> None:
    chapter_repo = FakeChapterRepository()
    llm = FakeLLMClient(knowledge={"period": "childhood"}, fail_generate=True)
    pipeline, _ = _build_pipeline(llm=llm, chapter_repo=chapter_repo)

    await pipeline.run(_input(transcript_on_device="원본 구술"))

    chapters = list(chapter_repo.by_id.values())
    assert len(chapters) == 1
    assert "정밀 재전사 결과" in chapters[0].body_text  # 이어붙이기 폴백 결과


async def test_second_upload_same_period_appends_to_existing_chapter() -> None:
    chapter_repo = FakeChapterRepository()
    llm = FakeLLMClient(knowledge={"period": "youth"})
    pipeline, _ = _build_pipeline(llm=llm, chapter_repo=chapter_repo)

    user_id = uuid.uuid4()
    await pipeline.run(_input(user_id=user_id))
    await pipeline.run(_input(user_id=user_id))

    chapters = [c for c in chapter_repo.by_id.values() if c.user_id == user_id]
    assert len(chapters) == 1  # 같은 시기는 같은 챕터로 귀속(단순화된 규칙)
    assert chapters[0].version == 2


async def test_resent_same_turn_is_idempotent() -> None:
    """sync-contract.md §2 — 같은 (user, session, turn)의 재전송/잡 재시도는
    새 청크를 만들지 않고, 챕터 윤문도 다시 돌지 않는다(version 안 오름)."""
    chapter_repo = FakeChapterRepository()
    chunk_repo = FakeConversationChunkRepository()
    llm = FakeLLMClient(knowledge={"period": "youth"})
    pipeline, _ = _build_pipeline(llm=llm, chapter_repo=chapter_repo, chunk_repo=chunk_repo)

    user_id = uuid.uuid4()
    first = await pipeline.run(_input(user_id=user_id, device_session_id="sess-1", turn_id=3))
    second = await pipeline.run(_input(user_id=user_id, device_session_id="sess-1", turn_id=3))

    assert second.id == first.id
    assert len(chunk_repo._store) == 1  # noqa: SLF001
    chapters = [c for c in chapter_repo.by_id.values() if c.user_id == user_id]
    assert len(chapters) == 1
    assert chapters[0].version == 1  # 두 번째 실행은 save_draft를 아예 호출 안 함
