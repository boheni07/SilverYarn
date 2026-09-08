"""Invitation 도메인 엔티티 — schema.md §5 `invitations` 테이블 매핑."""

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID

from core_service.shared.domain_enums import FamilyRole

# 비즈니스 결정 없이 정한 편의값 — decisions.md 미등재, Do 단계 재확인 필요
DEFAULT_EXPIRY_DAYS = 7


class InvitationStatus(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    EXPIRED = "expired"


@dataclass
class Invitation:
    id: UUID
    user_id: UUID
    invited_by: UUID | None
    contact: str
    role: FamilyRole
    token: str
    status: InvitationStatus
    created_at: datetime
    expires_at: datetime

    def is_expired(self, now: datetime | None = None) -> bool:
        return (now or datetime.now(UTC)) >= self.expires_at

    def ensure_acceptable(self, now: datetime | None = None) -> None:
        """비즈니스 규칙: pending 상태 + 만료 전이어야 수락 가능."""
        if self.status != InvitationStatus.PENDING:
            raise ValueError(f"이미 처리된 초대입니다(상태: {self.status.value}).")
        if self.is_expired(now):
            raise ValueError("만료된 초대입니다.")
