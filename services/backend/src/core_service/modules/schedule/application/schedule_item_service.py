"""ScheduleItem 유스케이스 — 비서 모드(일정/복약)."""

import uuid
from datetime import datetime

from core_service.core.errors import ApiError
from core_service.modules.schedule.domain.schedule_item import (
    ScheduleItem,
    ScheduleKind,
    ScheduleStatus,
)
from core_service.modules.schedule.infrastructure.schedule_item_repository import (
    ScheduleItemRepository,
)


class ScheduleItemService:
    def __init__(self, repo: ScheduleItemRepository):
        self._repo = repo

    async def get_schedule_item(self, schedule_item_id: uuid.UUID) -> ScheduleItem:
        item = await self._repo.get_by_id(schedule_item_id)
        if item is None:
            raise ApiError("NOT_FOUND", f"일정/복약 항목({schedule_item_id})을 찾을 수 없습니다.")
        return item

    async def list_schedule_items_for_user(self, user_id: uuid.UUID) -> list[ScheduleItem]:
        return await self._repo.list_by_user(user_id)

    async def list_pending_schedule_items_for_user(self, user_id: uuid.UUID) -> list[ScheduleItem]:
        """GET /sync/download가 쓰는 조회 — sync-contract.md §5."""
        return await self._repo.list_pending_by_user(user_id)

    async def create_schedule_item(
        self,
        user_id: uuid.UUID,
        kind: ScheduleKind,
        due_at: datetime,
        description: str | None = None,
        location: str | None = None,
        recurrence: str | None = None,
    ) -> ScheduleItem:
        if description is not None and len(description) > 300:
            raise ApiError("VALIDATION_ERROR", "description은 최대 300자입니다.")
        if location is not None and len(location) > 200:
            raise ApiError("VALIDATION_ERROR", "location은 최대 200자입니다.")
        return await self._repo.create(
            user_id=user_id,
            kind=kind,
            due_at=due_at,
            description=description,
            location=location,
            recurrence=recurrence,
        )

    async def respond(
        self,
        schedule_item_id: uuid.UUID,
        status: ScheduleStatus,
        decline_reason: str | None = None,
    ) -> ScheduleItem:
        """확정(confirmed)/누락(missed)/거절(declined) 응답 처리.

        pending 상태만 응답 가능(Chapter.ensure_reviewable과 동일한 재응답 방지
        원칙) — 이미 처리된 항목에 대한 중복/모순 응답을 막는다.
        """
        if status == ScheduleStatus.DECLINED and not decline_reason:
            raise ApiError("VALIDATION_ERROR", "거절 시 decline_reason이 필요합니다.")
        if status == ScheduleStatus.PENDING:
            raise ApiError("VALIDATION_ERROR", "PENDING으로는 응답할 수 없습니다.")

        item = await self.get_schedule_item(schedule_item_id)
        try:
            item.ensure_respondable()
        except ValueError as exc:
            raise ApiError("CONFLICT", str(exc)) from exc

        return await self._repo.respond(schedule_item_id, status, decline_reason)

    async def schedule_next_reminder(
        self, schedule_item_id: uuid.UUID, next_remind_at: datetime
    ) -> ScheduleItem:
        await self.get_schedule_item(schedule_item_id)  # 존재 확인
        return await self._repo.schedule_next_reminder(schedule_item_id, next_remind_at)
