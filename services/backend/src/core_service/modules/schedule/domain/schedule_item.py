"""ScheduleItem 도메인 엔티티 — schema.md §5 `schedule_items` 테이블 매핑.

⚠️ 골격 단계: Repository/Service/API 미구현.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class ScheduleKind(StrEnum):
    APPOINTMENT = "appointment"
    MEDICATION = "medication"


class ScheduleStatus(StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    MISSED = "missed"
    DECLINED = "declined"


@dataclass
class ScheduleItem:
    id: UUID
    user_id: UUID
    kind: ScheduleKind
    description: str | None
    location: str | None
    recurrence: str | None
    due_at: datetime
    status: ScheduleStatus
    remind_count: int
    next_remind_at: datetime | None
    decline_reason: str | None
    responded_at: datetime | None
