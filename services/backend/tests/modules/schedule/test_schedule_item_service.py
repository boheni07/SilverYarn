"""ScheduleItemService 유닛 테스트 — 페이크 Repository로 DB 없이 Application 계층 검증."""

import uuid
from datetime import datetime, timedelta

import pytest

from core_service.core.errors import ApiError
from core_service.modules.schedule.application.schedule_item_service import ScheduleItemService
from core_service.modules.schedule.domain.schedule_item import (
    ScheduleItem,
    ScheduleKind,
    ScheduleStatus,
)


class FakeScheduleItemRepository:
    def __init__(self) -> None:
        self._store: dict[uuid.UUID, ScheduleItem] = {}

    async def get_by_id(self, schedule_item_id: uuid.UUID) -> ScheduleItem | None:
        return self._store.get(schedule_item_id)

    async def list_by_user(self, user_id: uuid.UUID) -> list[ScheduleItem]:
        return sorted((i for i in self._store.values() if i.user_id == user_id), key=lambda i: i.due_at)

    async def create(
        self,
        user_id: uuid.UUID,
        kind: ScheduleKind,
        due_at: datetime,
        description: str | None = None,
        location: str | None = None,
        recurrence: str | None = None,
    ) -> ScheduleItem:
        item = ScheduleItem(
            id=uuid.uuid4(),
            user_id=user_id,
            kind=kind,
            description=description,
            location=location,
            recurrence=recurrence,
            due_at=due_at,
            status=ScheduleStatus.PENDING,
            remind_count=0,
            next_remind_at=None,
            decline_reason=None,
            responded_at=None,
        )
        self._store[item.id] = item
        return item

    async def respond(
        self, schedule_item_id: uuid.UUID, status: ScheduleStatus, decline_reason: str | None
    ) -> ScheduleItem:
        item = self._store[schedule_item_id]
        item.status = status
        item.decline_reason = decline_reason
        item.responded_at = datetime.now()
        return item

    async def schedule_next_reminder(
        self, schedule_item_id: uuid.UUID, next_remind_at: datetime
    ) -> ScheduleItem:
        item = self._store[schedule_item_id]
        item.next_remind_at = next_remind_at
        item.remind_count += 1
        return item


@pytest.fixture
def service() -> ScheduleItemService:
    return ScheduleItemService(FakeScheduleItemRepository())  # type: ignore[arg-type]


async def test_create_schedule_item_succeeds(service: ScheduleItemService) -> None:
    item = await service.create_schedule_item(
        user_id=uuid.uuid4(),
        kind=ScheduleKind.MEDICATION,
        due_at=datetime.now() + timedelta(hours=1),
        description="혈압약",
    )
    assert item.status == ScheduleStatus.PENDING
    assert item.remind_count == 0


async def test_create_schedule_item_rejects_long_description(service: ScheduleItemService) -> None:
    with pytest.raises(ApiError) as exc_info:
        await service.create_schedule_item(
            user_id=uuid.uuid4(),
            kind=ScheduleKind.APPOINTMENT,
            due_at=datetime.now(),
            description="x" * 301,
        )
    assert exc_info.value.code == "VALIDATION_ERROR"


async def test_respond_confirmed_succeeds(service: ScheduleItemService) -> None:
    item = await service.create_schedule_item(
        user_id=uuid.uuid4(), kind=ScheduleKind.APPOINTMENT, due_at=datetime.now()
    )
    result = await service.respond(item.id, ScheduleStatus.CONFIRMED)
    assert result.status == ScheduleStatus.CONFIRMED
    assert result.responded_at is not None


async def test_respond_declined_without_reason_rejected(service: ScheduleItemService) -> None:
    item = await service.create_schedule_item(
        user_id=uuid.uuid4(), kind=ScheduleKind.APPOINTMENT, due_at=datetime.now()
    )
    with pytest.raises(ApiError) as exc_info:
        await service.respond(item.id, ScheduleStatus.DECLINED)
    assert exc_info.value.code == "VALIDATION_ERROR"


async def test_respond_declined_with_reason_succeeds(service: ScheduleItemService) -> None:
    item = await service.create_schedule_item(
        user_id=uuid.uuid4(), kind=ScheduleKind.APPOINTMENT, due_at=datetime.now()
    )
    result = await service.respond(item.id, ScheduleStatus.DECLINED, decline_reason="몸이 안 좋아서")
    assert result.status == ScheduleStatus.DECLINED
    assert result.decline_reason == "몸이 안 좋아서"


async def test_respond_with_pending_status_rejected(service: ScheduleItemService) -> None:
    item = await service.create_schedule_item(
        user_id=uuid.uuid4(), kind=ScheduleKind.APPOINTMENT, due_at=datetime.now()
    )
    with pytest.raises(ApiError) as exc_info:
        await service.respond(item.id, ScheduleStatus.PENDING)
    assert exc_info.value.code == "VALIDATION_ERROR"


async def test_respond_already_responded_raises_conflict(service: ScheduleItemService) -> None:
    item = await service.create_schedule_item(
        user_id=uuid.uuid4(), kind=ScheduleKind.APPOINTMENT, due_at=datetime.now()
    )
    await service.respond(item.id, ScheduleStatus.CONFIRMED)
    with pytest.raises(ApiError) as exc_info:
        await service.respond(item.id, ScheduleStatus.MISSED)
    assert exc_info.value.code == "CONFLICT"


async def test_schedule_next_reminder_increments_count(service: ScheduleItemService) -> None:
    item = await service.create_schedule_item(
        user_id=uuid.uuid4(), kind=ScheduleKind.MEDICATION, due_at=datetime.now()
    )
    next_time = datetime.now() + timedelta(minutes=30)
    result = await service.schedule_next_reminder(item.id, next_time)
    assert result.remind_count == 1
    assert result.next_remind_at == next_time


async def test_get_schedule_item_not_found(service: ScheduleItemService) -> None:
    with pytest.raises(ApiError) as exc_info:
        await service.get_schedule_item(uuid.uuid4())
    assert exc_info.value.code == "NOT_FOUND"


async def test_list_schedule_items_filters_by_user(service: ScheduleItemService) -> None:
    user_id = uuid.uuid4()
    other_id = uuid.uuid4()
    await service.create_schedule_item(user_id=user_id, kind=ScheduleKind.MEDICATION, due_at=datetime.now())
    await service.create_schedule_item(user_id=other_id, kind=ScheduleKind.MEDICATION, due_at=datetime.now())
    items = await service.list_schedule_items_for_user(user_id)
    assert len(items) == 1
    assert items[0].user_id == user_id
