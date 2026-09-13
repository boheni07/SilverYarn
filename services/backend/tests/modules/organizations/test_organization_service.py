"""OrganizationService 유닛 테스트 — 페이크 Repository로 DB 없이 Application 계층 검증.

decisions.md #59(I2, 2026-09-13) — B2G 시설 테넌시 안전망의 시설 CRUD.
"""

import uuid
from datetime import UTC, datetime

import pytest

from core_service.core.errors import ApiError
from core_service.modules.organizations.application.organization_service import (
    OrganizationService,
)
from core_service.modules.organizations.domain.organization import Organization


class FakeOrganizationRepository:
    def __init__(self) -> None:
        self._store: dict[uuid.UUID, Organization] = {}

    async def get_by_id(self, org_id: uuid.UUID) -> Organization | None:
        return self._store.get(org_id)

    async def list_all(self) -> list[Organization]:
        return sorted(self._store.values(), key=lambda o: o.created_at, reverse=True)

    async def create(self, name: str) -> Organization:
        org = Organization(id=uuid.uuid4(), name=name, created_at=datetime.now(UTC))
        self._store[org.id] = org
        return org

    async def exists(self, org_id: uuid.UUID) -> bool:
        return org_id in self._store


@pytest.fixture
def service() -> OrganizationService:
    return OrganizationService(FakeOrganizationRepository())  # type: ignore[arg-type]


async def test_create_organization_succeeds(service: OrganizationService) -> None:
    org = await service.create_organization("행복요양원")
    assert org.name == "행복요양원"
    assert org.id is not None


async def test_create_organization_rejects_empty_name(service: OrganizationService) -> None:
    with pytest.raises(ApiError, match="1~200자"):
        await service.create_organization("")


async def test_create_organization_rejects_too_long_name(service: OrganizationService) -> None:
    with pytest.raises(ApiError, match="1~200자"):
        await service.create_organization("가" * 201)


async def test_get_organization_not_found_raises_api_error(service: OrganizationService) -> None:
    with pytest.raises(ApiError, match="찾을 수 없습니다"):
        await service.get_organization(uuid.uuid4())


async def test_get_organization_returns_created(service: OrganizationService) -> None:
    created = await service.create_organization("행복요양원")
    fetched = await service.get_organization(created.id)
    assert fetched.id == created.id


async def test_list_organizations_returns_all(service: OrganizationService) -> None:
    await service.create_organization("행복요양원")
    await service.create_organization("은빛복지관")
    orgs = await service.list_organizations()
    assert {o.name for o in orgs} == {"행복요양원", "은빛복지관"}


async def test_ensure_exists_passes_for_real_org(service: OrganizationService) -> None:
    org = await service.create_organization("행복요양원")
    await service.ensure_exists(org.id)  # raise 안 하면 통과


async def test_ensure_exists_raises_for_missing_org(service: OrganizationService) -> None:
    with pytest.raises(ApiError, match="존재하지 않는 시설"):
        await service.ensure_exists(uuid.uuid4())
