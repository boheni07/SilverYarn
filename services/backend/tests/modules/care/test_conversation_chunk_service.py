"""ConversationChunkService 유닛 테스트 — 페이크 Repository로 DB 없이 Application 계층 검증."""

import uuid
from datetime import UTC, datetime

import pytest

from core_service.core.errors import ApiError
from core_service.modules.care.application.conversation_chunk_service import (
    ConversationChunkService,
)
from core_service.modules.care.domain.conversation_chunk import ConversationChunk, ConversationMode


class FakeConversationChunkRepository:
    def __init__(self) -> None:
        self._store: dict[uuid.UUID, ConversationChunk] = {}

    async def get_by_id(self, chunk_id: uuid.UUID) -> ConversationChunk | None:
        return self._store.get(chunk_id)

    async def find_by_turn(
        self, user_id: uuid.UUID, session_id: str, turn_id: int
    ) -> ConversationChunk | None:
        return next(
            (
                c
                for c in self._store.values()
                if c.user_id == user_id and c.session_id == session_id and c.turn_id == turn_id
            ),
            None,
        )

    async def list_by_user(
        self, user_id: uuid.UUID, limit: int = 50, offset: int = 0
    ) -> list[ConversationChunk]:
        matches = [c for c in self._store.values() if c.user_id == user_id]
        matches.sort(key=lambda c: c.created_at, reverse=True)
        return matches[offset : offset + limit]

    async def search_by_keyword(self, user_id: uuid.UUID, keyword: str) -> list[ConversationChunk]:
        return [
            c
            for c in self._store.values()
            if c.user_id == user_id and c.transcript_server and keyword in c.transcript_server
        ]

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
        meta_prosody: dict | None = None,
        linked_photo_id: uuid.UUID | None = None,
        assistant_response: str | None = None,
    ) -> ConversationChunk:
        chunk = ConversationChunk(
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
            mode=mode,
            assistant_response=assistant_response,
            created_at=datetime.now(UTC),
        )
        self._store[chunk.id] = chunk
        return chunk


@pytest.fixture
def service() -> ConversationChunkService:
    return ConversationChunkService(FakeConversationChunkRepository())  # type: ignore[arg-type]


async def test_record_chunk_succeeds(service: ConversationChunkService) -> None:
    chunk = await service.record_chunk(
        user_id=uuid.uuid4(),
        raw_audio_ref="opus/abc123.opus",
        transcript_on_device="오늘 날씨가 참 좋네요",
        mode=ConversationMode.CARE,
    )
    assert chunk.mode == ConversationMode.CARE
    assert chunk.transcript_on_device == "오늘 날씨가 참 좋네요"


async def test_record_chunk_rejects_empty_audio_ref(service: ConversationChunkService) -> None:
    with pytest.raises(ApiError) as exc_info:
        await service.record_chunk(
            user_id=uuid.uuid4(), raw_audio_ref="", transcript_on_device="발화", mode=None
        )
    assert exc_info.value.code == "VALIDATION_ERROR"


async def test_record_chunk_rejects_empty_transcript(service: ConversationChunkService) -> None:
    with pytest.raises(ApiError) as exc_info:
        await service.record_chunk(
            user_id=uuid.uuid4(), raw_audio_ref="opus/x.opus", transcript_on_device="", mode=None
        )
    assert exc_info.value.code == "VALIDATION_ERROR"


async def test_get_chunk_not_found(service: ConversationChunkService) -> None:
    with pytest.raises(ApiError) as exc_info:
        await service.get_chunk(uuid.uuid4())
    assert exc_info.value.code == "NOT_FOUND"


async def test_list_chunks_for_user_filters_by_user(service: ConversationChunkService) -> None:
    user_id = uuid.uuid4()
    other_id = uuid.uuid4()
    await service.record_chunk(user_id=user_id, raw_audio_ref="a.opus", transcript_on_device="A", mode=None)
    await service.record_chunk(user_id=other_id, raw_audio_ref="b.opus", transcript_on_device="B", mode=None)
    chunks = await service.list_chunks_for_user(user_id)
    assert len(chunks) == 1
    assert chunks[0].transcript_on_device == "A"


async def test_list_chunks_rejects_invalid_limit(service: ConversationChunkService) -> None:
    with pytest.raises(ApiError) as exc_info:
        await service.list_chunks_for_user(uuid.uuid4(), limit=0)
    assert exc_info.value.code == "VALIDATION_ERROR"

    with pytest.raises(ApiError) as exc_info:
        await service.list_chunks_for_user(uuid.uuid4(), limit=201)
    assert exc_info.value.code == "VALIDATION_ERROR"


async def test_search_chunks_rejects_empty_keyword(service: ConversationChunkService) -> None:
    with pytest.raises(ApiError) as exc_info:
        await service.search_chunks(uuid.uuid4(), "")
    assert exc_info.value.code == "VALIDATION_ERROR"


async def test_search_chunks_matches_transcript_server(service: ConversationChunkService) -> None:
    user_id = uuid.uuid4()
    await service.record_chunk(
        user_id=user_id,
        raw_audio_ref="a.opus",
        transcript_on_device="원본",
        transcript_server="1978년 인천 공장 이야기",
        mode=ConversationMode.AUTHOR,
    )
    await service.record_chunk(
        user_id=user_id,
        raw_audio_ref="b.opus",
        transcript_on_device="원본2",
        transcript_server="전혀 다른 내용",
        mode=ConversationMode.AUTHOR,
    )
    results = await service.search_chunks(user_id, "인천")
    assert len(results) == 1
    assert "인천" in results[0].transcript_server
