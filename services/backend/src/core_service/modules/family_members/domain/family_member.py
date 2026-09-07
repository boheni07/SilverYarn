"""FamilyMember 도메인 엔티티 — schema.md §5 `family_members` 테이블 매핑.

glossary.md: "가족"/"복지사"/"요양보호사"는 모두 이 테이블의 서로 다른 role 값으로
표현한다. RBAC 매트릭스는 design.md §7.1 참조.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class FamilyRole(StrEnum):
    FAMILY = "family"
    CAREGIVER = "caregiver"
    SOCIAL_WORKER = "social_worker"
    ADMIN = "admin"


@dataclass
class FamilyMember:
    id: UUID
    user_id: UUID
    role: FamilyRole
    name: str
    contact: str
    two_factor_enabled: bool
    created_at: datetime
