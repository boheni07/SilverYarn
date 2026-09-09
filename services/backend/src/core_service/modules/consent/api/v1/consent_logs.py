"""consent_logs 리소스 라우터 — design.md §2.9 온보딩 동의 단계.

design.md §4.2 표에는 `GET /users/{userId}/consent-logs` 하나만 있으나, 동의를
'기록'하는 경로가 어디에도 없으면 온보딩 흐름(§2.9)이 성립하지 않아
`POST /users/{userId}/consent-logs`를 함께 추가한다(다음 문서 동기화 라운드에 §4.2 반영).

인가: POST는 "2FA + Role(family) 또는 Device Token" — 어르신 기기가 온보딩 중 본인
동의를 직접 남기거나(Device Token, `granted_by` 없음 = self), 가족이 웹 콘솔에서 대리
동의를 남긴다(2FA + family, `granted_by` = 본인 family_members.id = proxy).
GET은 design.md §4.2대로 2FA + Role.
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from core_service.core.auth import (
    WRITE_ELDER_DATA_ROLES,
    AuthContext,
    Principal,
    authorize_user_access,
    require_auth,
    require_principal,
)
from core_service.core.errors import ApiError
from core_service.modules.consent.application.consent_service import ConsentService
from core_service.modules.consent.deps import get_consent_service
from core_service.modules.consent.domain.consent_log import ConsentLog, ConsentType
from core_service.modules.family_members.application.family_member_service import FamilyMemberService
from core_service.modules.family_members.deps import get_family_member_service
from core_service.shared.schemas import DataResponse

router = APIRouter(tags=["consent_logs"])


class ConsentRecordRequest(BaseModel):
    consent_type: ConsentType
    granted: bool
    # 가족 대리 동의일 때만 채운다. 없으면 어르신 본인 동의(self)로 간주.
    granted_by: uuid.UUID | None = None


class ConsentLogResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    consent_type: str
    granted: bool
    granted_by: uuid.UUID | None
    actor: str  # "self" | "proxy" — granted_by 유무에서 파생(CTO 검토 B2)
    granted_at: datetime


def _to_response(log: ConsentLog) -> ConsentLogResponse:
    return ConsentLogResponse(
        id=log.id,
        user_id=log.user_id,
        consent_type=log.consent_type.value,
        granted=log.granted,
        granted_by=log.granted_by,
        actor=log.actor.value,
        granted_at=log.granted_at,
    )


@router.post(
    "/users/{user_id}/consent-logs",
    response_model=DataResponse[ConsentLogResponse],
    status_code=201,
)
async def record_consent(
    user_id: uuid.UUID,
    body: ConsentRecordRequest,
    service: ConsentService = Depends(get_consent_service),
    family_service: FamilyMemberService = Depends(get_family_member_service),
    principal: Principal = Depends(require_principal),
) -> DataResponse[ConsentLogResponse]:
    """design.md §2.9 — 개인정보 수집 동의(또는 철회) 1건 기록.

    어르신 기기(Device Token, `granted_by` 없음=self) 또는 가족 대리(2FA+family/admin,
    `granted_by`=본인 구성원 id=proxy). 대리 동의자는 반드시 호출자 본인의 구성원이어야 한다.
    """
    authorize_user_access(principal, user_id, allowed_roles=WRITE_ELDER_DATA_ROLES)
    if body.granted_by is not None:
        if isinstance(principal, AuthContext) and not principal.is_admin:
            caller_ids = {m.family_member_id for m in principal.memberships}
            if body.granted_by not in caller_ids:
                raise ApiError("FORBIDDEN", "다른 구성원 명의로 대리 동의를 남길 수 없습니다.")
        await family_service.get_family_member(body.granted_by)  # 없으면 NOT_FOUND
    log = await service.record_consent(
        user_id=user_id,
        consent_type=body.consent_type,
        granted=body.granted,
        granted_by=body.granted_by,
    )
    return DataResponse(data=_to_response(log))


@router.get(
    "/users/{user_id}/consent-logs",
    response_model=DataResponse[list[ConsentLogResponse]],
)
async def list_consent_logs(
    user_id: uuid.UUID,
    service: ConsentService = Depends(get_consent_service),
    ctx: AuthContext = Depends(require_auth),
) -> DataResponse[list[ConsentLogResponse]]:
    """design.md §4.2 — 동의 이력 조회 (L-12)."""
    authorize_user_access(ctx, user_id)
    logs = await service.list_consent_logs(user_id)
    return DataResponse(data=[_to_response(log) for log in logs])


class ConsentStateResponse(BaseModel):
    """유형별 현재 동의 상태 — 온보딩 완료 게이트·RBAC "동의 시" 조건용."""

    state: dict[str, bool]


@router.get(
    "/users/{user_id}/consent-state",
    response_model=DataResponse[ConsentStateResponse],
)
async def get_consent_state(
    user_id: uuid.UUID,
    service: ConsentService = Depends(get_consent_service),
    ctx: AuthContext = Depends(require_auth),
) -> DataResponse[ConsentStateResponse]:
    authorize_user_access(ctx, user_id)
    state = await service.current_state(user_id)
    return DataResponse(data=ConsentStateResponse(state={k.value: v for k, v in state.items()}))
