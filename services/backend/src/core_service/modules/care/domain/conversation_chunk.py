"""ConversationChunk 도메인 엔티티 — schema.md §5 `conversation_chunks` 테이블 매핑.

⚠️ 골격 단계: Repository/Service/API 미구현. `assistant_response`는 PII 암호화 대상
(schema.md §5, decisions.md #34) — 구현 시 애플리케이션 레벨 암호화 적용 필수.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class ConversationMode(StrEnum):
    AUTHOR = "author"
    CARE = "care"
    ASSIST = "assist"


@dataclass
class ConversationChunk:
    id: UUID
    user_id: UUID
    raw_audio_ref: str
    transcript_on_device: str
    transcript_server: str | None
    meta_period: str | None
    meta_people: list[str] | None
    meta_place: str | None
    meta_emotion: str | None
    linked_photo_id: UUID | None
    embedding_id: str | None  # Qdrant 포인터 — 진짜 FK 아님(erd.md §1)
    graph_node_ref: str | None  # Neo4j 포인터 — 진짜 FK 아님(erd.md §1)
    session_id: str | None
    turn_id: int | None
    mode: ConversationMode | None
    assistant_response: str | None  # PII, 암호화 대상 (schema.md §5)
    created_at: datetime
