"""FamilyMember 도메인 엔티티 — schema.md §5 `family_members` 테이블 매핑.

glossary.md: "가족"/"복지사"/"요양보호사"는 모두 이 테이블의 서로 다른 role 값으로
표현한다. RBAC 매트릭스는 design.md §7.1 참조.

FamilyRole은 `invitations.role`과 같은 Postgres enum을 공유하므로
`core_service.shared.domain_enums`에 정의돼 있다(두 모듈이 공동 소유) — 이 파일은
그대로 재노출해 기존 임포트 경로(`from ...family_member import FamilyRole`)를 유지한다.
"""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from core_service.shared.domain_enums import FamilyRole

__all__ = ["FamilyMember", "FamilyRole"]


@dataclass
class FamilyMember:
    id: UUID
    user_id: UUID
    role: FamilyRole
    name: str
    contact: str
    two_factor_enabled: bool
    keycloak_sub: str | None
    created_at: datetime
    # B2G 시설 소속 — decisions.md #59(I2, 2026-09-13). NULL = 개인(대부분의 가족).
    # 시설 소속 caregiver/social_worker만 채운다. organizations 모듈 참조는 순수
    # 도메인이 다른 모듈에 의존하면 안 되므로 UUID만 든다.
    org_id: UUID | None = None
