"""organizations 리소스 라우터 — decisions.md #59(I2), apps/admin "시설 관리" 화면용.

시설 생성·목록은 admin 전용(design.md §7.1과 동일하게 "관리자만 다루는 리소스"로
분류 — 시설 등록 자체가 B2G 영업/계약 프로세스의 결과라 운영자만 다룬다).
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from core_service.auth_deps import require_roles
from core_service.modules.organizations.application.organization_service import (
    OrganizationService,
)
from core_service.modules.organizations.deps import get_organization_service
from core_service.shared.domain_enums import FamilyRole
from core_service.shared.schemas import DataResponse

router = APIRouter(prefix="/organizations", tags=["organizations"])


class OrganizationCreateRequest(BaseModel):
    name: str


class OrganizationResponse(BaseModel):
    id: uuid.UUID
    name: str
    created_at: datetime


def _to_response(org) -> OrganizationResponse:  # noqa: ANN001 — Organization 도메인 dataclass
    return OrganizationResponse(id=org.id, name=org.name, created_at=org.created_at)


@router.get("", response_model=DataResponse[list[OrganizationResponse]])
async def list_organizations(
    service: OrganizationService = Depends(get_organization_service),
    _admin=Depends(require_roles(FamilyRole.ADMIN)),  # noqa: ANN001
) -> DataResponse[list[OrganizationResponse]]:
    orgs = await service.list_organizations()
    return DataResponse(data=[_to_response(o) for o in orgs])


@router.post("", response_model=DataResponse[OrganizationResponse], status_code=201)
async def create_organization(
    body: OrganizationCreateRequest,
    service: OrganizationService = Depends(get_organization_service),
    _admin=Depends(require_roles(FamilyRole.ADMIN)),  # noqa: ANN001
) -> DataResponse[OrganizationResponse]:
    org = await service.create_organization(body.name)
    return DataResponse(data=_to_response(org))


@router.get("/{org_id}", response_model=DataResponse[OrganizationResponse])
async def get_organization(
    org_id: uuid.UUID,
    service: OrganizationService = Depends(get_organization_service),
    _admin=Depends(require_roles(FamilyRole.ADMIN)),  # noqa: ANN001
) -> DataResponse[OrganizationResponse]:
    org = await service.get_organization(org_id)
    return DataResponse(data=_to_response(org))
