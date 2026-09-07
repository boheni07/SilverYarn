"""ScheduleItem 도메인 엔티티 — schema.md §5 `schedule_items` 테이블 매핑.

sync-contract.md §3의 필드 단위 충돌정책 대상이다: `due_at`/`description`/
`location`/`recurrence` 등 콘텐츠 필드는 Server-Wins, `status`/`responded_at`
(단말에서 어르신이 직접 "복약 완료"를 누른 결과)은 Device-Wins로 분리해야
한다 — 이 모듈은 그 구분을 아직 동기화 계층에 반영하지 않았고(sync 모듈이
아직 골격 단계라 실제 업/다운로드 병합 로직 자체가 없음), 서버 API를 통한
갱신 규칙만 우선 구현한다.
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


# 응답(response)을 받을 수 있는 상태 — 이미 확정/누락/거절 처리된 항목은
# 다시 응답받지 않는다(재알림이 필요하면 별도로 next_remind_at만 갱신).
RESPONDABLE_STATUSES = frozenset({ScheduleStatus.PENDING})


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

    def ensure_respondable(self) -> None:
        """비즈니스 규칙: pending 상태만 응답(확정/누락/거절) 가능."""
        if self.status not in RESPONDABLE_STATUSES:
            raise ValueError(f"이미 응답 처리된 일정입니다(현재 상태: {self.status.value}).")
