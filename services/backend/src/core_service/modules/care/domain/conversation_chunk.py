"""ConversationChunk 도메인 엔티티 — schema.md §5 `conversation_chunks` 테이블 매핑.

`assistant_response`는 PII 암호화 대상(schema.md §5, decisions.md #34) — 애플리케이션
레벨 암호화 방식은 아직 미확정(schema.md §8 Next Steps)이라 이 모듈은 평문으로
다룬다. 실제 암호화 적용 전까지 로그에 이 필드를 출력하지 않도록 core/logging.py
사용 시 주의(별도 마스킹 유틸은 Do 단계에서 추가).

이 모듈은 대화 청크의 조회만 다룬다(불변 로그 성격 — 생성은 sync 파이프라인,
갱신은 없음). emotion_alerts/emotion_scores는 Phase 1 피처플래그 OFF(decisions.md
#25)라 이 라운드에서 구현하지 않는다.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any
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
    meta_prosody: dict[str, Any] | None
    linked_photo_id: UUID | None
    embedding_id: str | None  # Qdrant 포인터 — 진짜 FK 아님(erd.md §1)
    graph_node_ref: str | None  # Neo4j 포인터 — 진짜 FK 아님(erd.md §1)
    session_id: str | None
    turn_id: int | None
    mode: ConversationMode | None
    assistant_response: str | None  # PII, 암호화 대상 (schema.md §5)
    created_at: datetime
