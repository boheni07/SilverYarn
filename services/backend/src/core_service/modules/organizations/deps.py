"""organizations 모듈의 공개 조합 지점 — family_members/deps.py와 동일한 패턴."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core_service.core.db import get_db
from core_service.modules.organizations.application.organization_service import (
    OrganizationService,
)
from core_service.modules.organizations.infrastructure.organization_repository import (
    OrganizationRepository,
)


def get_organization_service(session: AsyncSession = Depends(get_db)) -> OrganizationService:
    return OrganizationService(OrganizationRepository(session))
