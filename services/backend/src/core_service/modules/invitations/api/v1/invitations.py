"""invitations 리소스 라우터.

design.md §4.2에 있는 것은 `POST /invitations` 하나뿐이다. 아래 조회(`GET
/invitations/{token}`)와 수락(`POST /invitations/{token}/accept`)은 스캐폴딩
시점 추가 — 초대를 만들기만 하고 수락 경로가 없으면 온보딩이 끝나지 않는다.
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core_service.auth_deps import (
    WRITE_ELDER_DATA_ROLES,
    AuthContext,
    VerifiedSubject,
    authorize_user_access,
    require_auth,
    require_verified_subject,
)
from core_service.core.db import get_db
from core_service.core.errors import ApiError
from core_service.modules.family_members.application.family_member_service import (
    FamilyMemberService,
)
from core_service.modules.family_members.deps import get_family_member_service
from core_service.modules.invitations.application.invitation_service import InvitationService
from core_service.modules.invitations.infrastructure.invitation_repository import (
    InvitationRepository,
)
from core_service.shared.domain_enums import FamilyRole
from core_service.shared.schemas import DataResponse

router = APIRouter(prefix="/invitations", tags=["invitations"])


class InvitationCreateRequest(BaseModel):
    user_id: uuid.UUID
    invited_by: uuid.UUID | None = None
    contact: str
    role: FamilyRole


class InvitationResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    invited_by: uuid.UUID | None
    contact: str
    role: str
    token: str
    status: str
    created_at: datetime
    expires_at: datetime


class InvitationAcceptRequest(BaseModel):
    """수락 시점에 초대받은 사람의 이름을 받는다 — invitations 테이블엔 name이 없다
    (contact만 저장), family_members.name은 NOT NULL이라 이 시점에 채워야 한다."""

    name: str


def _service(session: AsyncSession = Depends(get_db)) -> InvitationService:
    return InvitationService(InvitationRepository(session))


def _to_response(invitation) -> InvitationResponse:  # noqa: ANN001 — Invitation 도메인 dataclass
    return InvitationResponse(
        id=invitation.id,
        user_id=invitation.user_id,
        invited_by=invitation.invited_by,
        contact=invitation.contact,
        role=invitation.role.value,
        token=invitation.token,
        status=invitation.status.value,
        created_at=invitation.created_at,
        expires_at=invitation.expires_at,
    )


@router.post("", response_model=DataResponse[InvitationResponse], status_code=201)
async def create_invitation(
    body: InvitationCreateRequest,
    service: InvitationService = Depends(_service),
    family_service: FamilyMemberService = Depends(get_family_member_service),
    ctx: AuthContext = Depends(require_auth),
) -> DataResponse[InvitationResponse]:
    """design.md §4.2 — 가족 구성원 초대. 초대는 접근 권한 부여이므로 family/admin + 2FA.
    `invited_by`가 오면 호출자 본인의 구성원 id여야 한다(타인 명의 초대 방지)."""
    authorize_user_access(ctx, body.user_id, allowed_roles=WRITE_ELDER_DATA_ROLES)
    if body.invited_by is not None:
        if not ctx.is_admin and body.invited_by not in {m.family_member_id for m in ctx.memberships}:
            raise ApiError("FORBIDDEN", "다른 구성원 명의로 초대할 수 없습니다.")
        await family_service.get_family_member(body.invited_by)  # 존재하지 않으면 NOT_FOUND
    invitation = await service.create_invitation(
        user_id=body.user_id, invited_by=body.invited_by, contact=body.contact, role=body.role
    )
    return DataResponse(data=_to_response(invitation))


@router.get("/{token}", response_model=DataResponse[InvitationResponse])
async def get_invitation(
    token: str,
    service: InvitationService = Depends(_service),
) -> DataResponse[InvitationResponse]:
    """초대받은 사람이 수락 전 내용(누가·어떤 역할로 초대했는지) 확인용. 인증 불필요
    — 토큰 자체가 접근 권한이다(초대 링크 소유자만 알 수 있음)."""
    invitation = await service.get_invitation_by_token(token)
    return DataResponse(data=_to_response(invitation))


@router.post("/{token}/accept", response_model=DataResponse[InvitationResponse])
async def accept_invitation(
    token: str,
    body: InvitationAcceptRequest,
    service: InvitationService = Depends(_service),
    family_service: FamilyMemberService = Depends(get_family_member_service),
    subject: VerifiedSubject = Depends(require_verified_subject),
) -> DataResponse[InvitationResponse]:
    """초대 수락 — pending/미만료 검증 후 accepted로 전이하고 family_members 행 생성.

    수락자는 Keycloak 로그인 상태여야 한다(토큰만 검증, 아직 family_member 연결 전이라
    require_family은 못 씀). 토큰 `sub`를 새 family_member의 `keycloak_sub`로 박아넣어야
    이후 그 사람이 실제로 로그인해 앱을 쓸 수 있다 — 이게 없으면 계정 연결이 끊긴다.

    두 Repository가 같은 `Depends(get_db)` 세션을 공유하므로(FastAPI 요청별 캐싱)
    한 트랜잭션으로 묶인다: 초대 상태 갱신과 family_member 생성 중 하나가 실패하면
    둘 다 롤백된다.
    """
    invitation = await service.validate_and_consume(token)
    member = await family_service.create_family_member(
        user_id=invitation.user_id,
        role=invitation.role,
        name=body.name,
        contact=invitation.contact,
        keycloak_sub=subject.subject,
    )
    _ = member  # 응답은 초대 자체를 반환 — family_member 조회는 별도 엔드포인트(family_members 모듈)
    return DataResponse(data=_to_response(invitation))
