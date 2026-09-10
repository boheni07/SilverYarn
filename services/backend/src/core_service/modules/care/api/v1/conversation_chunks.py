"""conversation_chunks 리소스 라우터.

design.md §4.2에는 이 리소스의 엔드포인트가 없다(청크는 `/sync/upload` 파이프라인의
산출물이라 클라이언트가 직접 만들지 않음 — author의 chapters와 동일한 이유로 POST를
노출하지 않는다). 아래 3건은 조회·검색 목적의 스캐폴딩 시점 추가다.
"""

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core_service.auth_deps import AuthContext, authorize_user_access, require_auth
from core_service.core.db import get_db
from core_service.modules.care.application.conversation_chunk_service import (
    ConversationChunkService,
)
from core_service.modules.care.infrastructure.conversation_chunk_repository import (
    ConversationChunkRepository,
)
from core_service.shared.schemas import DataResponse

router = APIRouter(tags=["conversation-chunks"])


class ConversationChunkResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    transcript_on_device: str
    transcript_server: str | None
    meta_period: str | None
    meta_people: list[str] | None
    meta_place: str | None
    meta_emotion: str | None
    meta_prosody: dict[str, Any] | None
    linked_photo_id: uuid.UUID | None
    session_id: str | None
    turn_id: int | None
    mode: str | None
    # ⚠️ assistant_response는 PII(schema.md §5) — 관리자/디버그 용도 외에는 응답에
    # 포함하지 않는 것을 검토해야 한다(Do 단계, 암호화 방식 확정과 함께). 지금은
    # 스캐폴딩이라 그대로 노출한다.
    assistant_response: str | None
    created_at: datetime


def _service(session: AsyncSession = Depends(get_db)) -> ConversationChunkService:
    return ConversationChunkService(ConversationChunkRepository(session))


def _to_response(chunk) -> ConversationChunkResponse:  # noqa: ANN001 — 도메인 dataclass
    return ConversationChunkResponse(
        id=chunk.id,
        user_id=chunk.user_id,
        transcript_on_device=chunk.transcript_on_device,
        transcript_server=chunk.transcript_server,
        meta_period=chunk.meta_period,
        meta_people=chunk.meta_people,
        meta_place=chunk.meta_place,
        meta_emotion=chunk.meta_emotion,
        meta_prosody=chunk.meta_prosody,
        linked_photo_id=chunk.linked_photo_id,
        session_id=chunk.session_id,
        turn_id=chunk.turn_id,
        mode=chunk.mode.value if chunk.mode else None,
        assistant_response=chunk.assistant_response,
        created_at=chunk.created_at,
    )


@router.get(
    "/users/{user_id}/conversation-chunks", response_model=DataResponse[list[ConversationChunkResponse]]
)
async def list_conversation_chunks(
    user_id: uuid.UUID,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    service: ConversationChunkService = Depends(_service),
    ctx: AuthContext = Depends(require_auth),
) -> DataResponse[list[ConversationChunkResponse]]:
    authorize_user_access(ctx, user_id)
    chunks = await service.list_chunks_for_user(user_id, limit=limit, offset=offset)
    return DataResponse(data=[_to_response(c) for c in chunks])


@router.get(
    "/users/{user_id}/conversation-chunks/search",
    response_model=DataResponse[list[ConversationChunkResponse]],
)
async def search_conversation_chunks(
    user_id: uuid.UUID,
    keyword: str = Query(min_length=1),
    service: ConversationChunkService = Depends(_service),
    ctx: AuthContext = Depends(require_auth),
) -> DataResponse[list[ConversationChunkResponse]]:
    """⚠️ 임시 검색 — 실제 하이브리드 서치(Qdrant, design.md §2.4)로 교체 예정."""
    authorize_user_access(ctx, user_id)
    chunks = await service.search_chunks(user_id, keyword)
    return DataResponse(data=[_to_response(c) for c in chunks])


@router.get("/conversation-chunks/{chunk_id}", response_model=DataResponse[ConversationChunkResponse])
async def get_conversation_chunk(
    chunk_id: uuid.UUID,
    service: ConversationChunkService = Depends(_service),
    ctx: AuthContext = Depends(require_auth),
) -> DataResponse[ConversationChunkResponse]:
    chunk = await service.get_chunk(chunk_id)
    authorize_user_access(ctx, chunk.user_id)
    return DataResponse(data=_to_response(chunk))
