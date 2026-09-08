"""PhotoRequest 도메인 엔티티 — schema.md §3.7 `photo_requests` 테이블 매핑.

가족이 당사자에게 "사진을 더 올려달라"고 요청하는 흐름(WU3 → WF3 알림 생성).
design.md §4.2 F-3 예외 규칙 — invitations/photo-requests처럼 사전에 소유자를
특정할 수 없는 전역 생성 엔드포인트라 `/users/{userId}/...` 아래 중첩하지 않는다.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class PhotoRequestStatus(StrEnum):
    PENDING = "pending"
    FULFILLED = "fulfilled"
    DISMISSED = "dismissed"


@dataclass
class PhotoRequest:
    id: UUID
    user_id: UUID
    requested_by: UUID | None
    message: str | None
    status: PhotoRequestStatus
    created_at: datetime
    fulfilled_at: datetime | None

    def ensure_dismissable(self) -> None:
        """비즈니스 규칙: pending 상태에서만 dismiss 가능 — 이미 fulfilled/dismissed된
        요청을 다시 닫는 건 의미 없는 조작이라 막는다."""
        if self.status != PhotoRequestStatus.PENDING:
            raise ValueError(f"이미 처리된 요청입니다(상태: {self.status.value}).")
