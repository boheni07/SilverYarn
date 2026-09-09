"""schedule_items 리소스 라우터 — design.md §4.2 목록 1건(list, L-12)에 더해
생성/단건조회/응답/재알림 4건을 스캐폴딩 시점에 추가했다. chapters/conversation-chunks와
달리 POST를 노출한다 — 일정/복약은 AI 파이프라인 산출물이 아니라 가족·당사자가
직접 입력하는 리소스이기 때문이다(UI/UX 화면설계서 "일정/복약" 관리 화면 참조).
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core_service.core.auth import (
    WRITE_ELDER_DATA_ROLES,
    AuthContext,
    Principal,
    authorize_user_access,
    require_auth,
    require_principal,
)
from core_service.core.db import get_db
from core_service.modules.schedule.application.schedule_item_service import ScheduleItemService
from core_service.modules.schedule.domain.schedule_item import ScheduleKind, ScheduleStatus
from core_service.modules.schedule.infrastructure.schedule_item_repository import (
    ScheduleItemRepository,
)
from core_service.shared.schemas import DataResponse

router = APIRouter(tags=["schedule-items"])


class ScheduleItemCreateRequest(BaseModel):
    kind: ScheduleKind
    due_at: datetime
    description: str | None = None
    location: str | None = None
    recurrence: str | None = None


class ScheduleItemResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    kind: str
    description: str | None
    location: str | None
    recurrence: str | None
    due_at: datetime
    status: str
    remind_count: int
    next_remind_at: datetime | None
    decline_reason: str | None
    responded_at: datetime | None


class ScheduleItemRespondRequest(BaseModel):
    status: ScheduleStatus
    decline_reason: str | None = None


class ScheduleItemReminderRequest(BaseModel):
    next_remind_at: datetime


def _service(session: AsyncSession = Depends(get_db)) -> ScheduleItemService:
    return ScheduleItemService(ScheduleItemRepository(session))


def _to_response(item) -> ScheduleItemResponse:  # noqa: ANN001 — ScheduleItem 도메인 dataclass
    return ScheduleItemResponse(
        id=item.id,
        user_id=item.user_id,
        kind=item.kind.value,
        description=item.description,
        location=item.location,
        recurrence=item.recurrence,
        due_at=item.due_at,
        status=item.status.value,
        remind_count=item.remind_count,
        next_remind_at=item.next_remind_at,
        decline_reason=item.decline_reason,
        responded_at=item.responded_at,
    )


@router.get("/users/{user_id}/schedule-items", response_model=DataResponse[list[ScheduleItemResponse]])
async def list_schedule_items(
    user_id: uuid.UUID,
    service: ScheduleItemService = Depends(_service),
    ctx: AuthContext = Depends(require_auth),
) -> DataResponse[list[ScheduleItemResponse]]:
    """design.md §4.2 — 일정/복약 목록 조회(L-12)."""
    authorize_user_access(ctx, user_id)
    items = await service.list_schedule_items_for_user(user_id)
    return DataResponse(data=[_to_response(i) for i in items])


@router.post(
    "/users/{user_id}/schedule-items", response_model=DataResponse[ScheduleItemResponse], status_code=201
)
async def create_schedule_item(
    user_id: uuid.UUID,
    body: ScheduleItemCreateRequest,
    service: ScheduleItemService = Depends(_service),
    ctx: AuthContext = Depends(require_auth),
) -> DataResponse[ScheduleItemResponse]:
    authorize_user_access(ctx, user_id, allowed_roles=WRITE_ELDER_DATA_ROLES)
    item = await service.create_schedule_item(
        user_id=user_id,
        kind=body.kind,
        due_at=body.due_at,
        description=body.description,
        location=body.location,
        recurrence=body.recurrence,
    )
    return DataResponse(data=_to_response(item))


@router.get("/schedule-items/{schedule_item_id}", response_model=DataResponse[ScheduleItemResponse])
async def get_schedule_item(
    schedule_item_id: uuid.UUID,
    service: ScheduleItemService = Depends(_service),
    ctx: AuthContext = Depends(require_auth),
) -> DataResponse[ScheduleItemResponse]:
    item = await service.get_schedule_item(schedule_item_id)
    authorize_user_access(ctx, item.user_id)
    return DataResponse(data=_to_response(item))


@router.post("/schedule-items/{schedule_item_id}/respond", response_model=DataResponse[ScheduleItemResponse])
async def respond_schedule_item(
    schedule_item_id: uuid.UUID,
    body: ScheduleItemRespondRequest,
    service: ScheduleItemService = Depends(_service),
    principal: Principal = Depends(require_principal),
) -> DataResponse[ScheduleItemResponse]:
    """확정(confirmed)/누락(missed)/거절(declined) 응답 — pending 상태만 가능.

    어르신이 기기에서 리마인더에 응답하거나(Device Token) 가족이 웹에서 대신 처리한다.
    """
    item = await service.get_schedule_item(schedule_item_id)
    authorize_user_access(principal, item.user_id)
    item = await service.respond(
        schedule_item_id=schedule_item_id, status=body.status, decline_reason=body.decline_reason
    )
    return DataResponse(data=_to_response(item))


@router.post(
    "/schedule-items/{schedule_item_id}/next-reminder",
    response_model=DataResponse[ScheduleItemResponse],
)
async def schedule_next_reminder(
    schedule_item_id: uuid.UUID,
    body: ScheduleItemReminderRequest,
    service: ScheduleItemService = Depends(_service),
    ctx: AuthContext = Depends(require_auth),
) -> DataResponse[ScheduleItemResponse]:
    item = await service.get_schedule_item(schedule_item_id)
    authorize_user_access(ctx, item.user_id, allowed_roles=WRITE_ELDER_DATA_ROLES)
    item = await service.schedule_next_reminder(schedule_item_id, body.next_remind_at)
    return DataResponse(data=_to_response(item))
