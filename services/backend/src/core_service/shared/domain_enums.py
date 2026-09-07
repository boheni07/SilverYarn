"""여러 모듈이 공유하는 도메인 값 객체(enum) — DB enum 하나를 2개 이상의 모듈이 함께
참조할 때만 여기 둔다. 예: `family_role`은 `family_members.role`과 `invitations.role`
양쪽 테이블이 같은 Postgres enum을 쓴다(schema.md §5) — 어느 한쪽 모듈이 소유하면
다른 쪽이 그 모듈의 domain/을 import해야 하는 교차 결합이 생기므로 공유 커널로 뺐다.

⚠️ 이 파일에 도메인 엔티티(dataclass)를 두지 않는다 — 순수 값 객체(enum)만 허용.
"""

from enum import StrEnum


class FamilyRole(StrEnum):
    FAMILY = "family"
    CAREGIVER = "caregiver"
    SOCIAL_WORKER = "social_worker"
    ADMIN = "admin"
