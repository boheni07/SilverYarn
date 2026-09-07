"""family_members 모듈의 공개 조합 지점(composition point).

다른 모듈이 이 모듈의 Service가 필요하면(예: author 모듈이 챕터 감수자를 검증할 때)
이 파일만 import한다 — `infrastructure/`나 `api/`의 내부 구현을 직접 건드리지 않는다.
structure.md §2 모듈 경계 규칙("다른 모듈의 infrastructure/를 직접 import하지 않는다")을
모듈 간 Application 계층 재사용에도 동일하게 적용한 것.
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core_service.core.db import get_db
from core_service.modules.family_members.application.family_member_service import (
    FamilyMemberService,
)
from core_service.modules.family_members.infrastructure.family_member_repository import (
    FamilyMemberRepository,
)


def get_family_member_service(session: AsyncSession = Depends(get_db)) -> FamilyMemberService:
    return FamilyMemberService(FamilyMemberRepository(session))
