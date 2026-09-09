"""family_members 리소스 라우터.

design.md §4.2에는 family_members 직접 CRUD 엔드포인트가 없다(정식 온보딩은
`POST /api/v1/invitations` 수락 흐름 예정, 아직 미구현). 아래 2건은 그 전 단계를
메우기 위한 스캐폴딩 시점 추가다 — invitations 모듈 구현 후 재검토 필요.
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from core_service.core.auth import (
    WRITE_ELDER_DATA_ROLES,
    AuthContext,
    authorize_user_access,
    require_auth,
)
from core_service.modules.family_members.application.family_member_service import (
    FamilyMemberService,
)
from core_service.modules.family_members.deps import get_family_member_service
from core_service.modules.family_members.domain.family_member import FamilyRole
from core_service.shared.schemas import DataResponse

router = APIRouter(prefix="/users/{user_id}/family-members", tags=["family-members"])


class FamilyMemberCreateRequest(BaseModel):
    role: FamilyRole
    name: str
    contact: str


class FamilyMemberResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    role: str
    name: str
    contact: str
    two_factor_enabled: bool
    created_at: datetime


def _to_response(member) -> FamilyMemberResponse:  # noqa: ANN001 — FamilyMember 도메인 dataclass
    return FamilyMemberResponse(
        id=member.id,
        user_id=member.user_id,
        role=member.role.value,
        name=member.name,
        contact=member.contact,
        two_factor_enabled=member.two_factor_enabled,
        created_at=member.created_at,
    )


@router.get("", response_model=DataResponse[list[FamilyMemberResponse]])
async def list_family_members(
    user_id: uuid.UUID,
    service: FamilyMemberService = Depends(get_family_member_service),
    ctx: AuthContext = Depends(require_auth),
) -> DataResponse[list[FamilyMemberResponse]]:
    # 다른 구성원의 contact(전화번호)가 담기므로 family/admin만 (design.md §7.1 "가족구성원 설정").
    authorize_user_access(ctx, user_id, allowed_roles=WRITE_ELDER_DATA_ROLES)
    members = await service.list_family_members_for_user(user_id)
    return DataResponse(data=[_to_response(m) for m in members])


@router.post("", response_model=DataResponse[FamilyMemberResponse], status_code=201)
async def create_family_member(
    user_id: uuid.UUID,
    body: FamilyMemberCreateRequest,
    service: FamilyMemberService = Depends(get_family_member_service),
    ctx: AuthContext = Depends(require_auth),
) -> DataResponse[FamilyMemberResponse]:
    """임시 직접생성 — 정식 경로(초대 수락)는 invitations 모듈 구현 후 대체 예정.

    구성원 추가는 곧 접근 권한 부여이므로 family/admin + 2FA만.
    """
    authorize_user_access(ctx, user_id, allowed_roles=WRITE_ELDER_DATA_ROLES)
    member = await service.create_family_member(
        user_id=user_id, role=body.role, name=body.name, contact=body.contact
    )
    return DataResponse(data=_to_response(member))
