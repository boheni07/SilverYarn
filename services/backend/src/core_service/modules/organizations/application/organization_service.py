"""Organization 유스케이스."""

import uuid

from core_service.core.errors import ApiError
from core_service.modules.organizations.domain.organization import Organization
from core_service.modules.organizations.infrastructure.organization_repository import (
    OrganizationRepository,
)


class OrganizationService:
    def __init__(self, repo: OrganizationRepository):
        self._repo = repo

    async def get_organization(self, org_id: uuid.UUID) -> Organization:
        org = await self._repo.get_by_id(org_id)
        if org is None:
            raise ApiError("NOT_FOUND", f"시설({org_id})을 찾을 수 없습니다.")
        return org

    async def list_organizations(self) -> list[Organization]:
        return await self._repo.list_all()

    async def create_organization(self, name: str) -> Organization:
        if not name or len(name) > 200:
            raise ApiError("VALIDATION_ERROR", "name은 1~200자여야 합니다.")
        return await self._repo.create(name)

    async def ensure_exists(self, org_id: uuid.UUID) -> None:
        """다른 모듈(users/family_members)이 org_id를 배정하기 전 존재 확인용."""
        if not await self._repo.exists(org_id):
            raise ApiError("VALIDATION_ERROR", f"존재하지 않는 시설({org_id})입니다.")
