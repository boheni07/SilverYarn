"""photo_requests 리소스 라우터.

design.md §4.2에 있는 것은 `POST /photo-requests` 하나뿐이다(F-3 예외 — 소유자를
사전에 특정할 수 없는 전역 생성 엔드포인트). invitations 모듈과 같은 이유로 조회
(`GET /users/{userId}/photo-requests`)와 종료(`POST /photo-requests/{id}/dismiss`)를
스캐폴딩 시점에 추가했다 — 요청을 만들기만 하고 당사자가 볼 방법도, "필요없다"고
닫을 방법도 없으면 WU3(당사자 알림) → WF3(가족 확인) 루프가 끝나지 않는다.
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core_service.auth_deps import (
    WRITE_ELDER_DATA_ROLES,
    AuthContext,
    Principal,
    authorize_user_access,
    require_auth,
    require_principal,
)
from core_service.core.db import get_db
from core_service.core.errors import ApiError
from core_service.modules.family_members.application.family_member_service import (
    FamilyMemberService,
)
from core_service.modules.family_members.deps import get_family_member_service
from core_service.modules.photo_requests.application.photo_request_service import PhotoRequestService
from core_service.modules.photo_requests.domain.photo_request import PhotoRequest
from core_service.modules.photo_requests.infrastructure.photo_request_repository import (
    PhotoRequestRepository,
)
from core_service.shared.schemas import DataResponse

router = APIRouter(tags=["photo_requests"])


class PhotoRequestCreateRequest(BaseModel):
    user_id: uuid.UUID
    requested_by: uuid.UUID | None = None
    message: str | None = None


class PhotoRequestResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    requested_by: uuid.UUID | None
    message: str | None
    status: str
    created_at: datetime
    fulfilled_at: datetime | None


def _service(session: AsyncSession = Depends(get_db)) -> PhotoRequestService:
    return PhotoRequestService(PhotoRequestRepository(session))


def _to_response(request: PhotoRequest) -> PhotoRequestResponse:
    return PhotoRequestResponse(
        id=request.id,
        user_id=request.user_id,
        requested_by=request.requested_by,
        message=request.message,
        status=request.status.value,
        created_at=request.created_at,
        fulfilled_at=request.fulfilled_at,
    )


@router.post("/photo-requests", response_model=DataResponse[PhotoRequestResponse], status_code=201)
async def create_photo_request(
    body: PhotoRequestCreateRequest,
    service: PhotoRequestService = Depends(_service),
    family_service: FamilyMemberService = Depends(get_family_member_service),
    ctx: AuthContext = Depends(require_auth),
) -> DataResponse[PhotoRequestResponse]:
    """design.md §4.2 — 가족→당사자 사진 추가 요청. family/admin + 2FA."""
    authorize_user_access(ctx, body.user_id, allowed_roles=WRITE_ELDER_DATA_ROLES)
    if body.requested_by is not None:
        if not ctx.is_admin and body.requested_by not in {m.family_member_id for m in ctx.memberships}:
            raise ApiError("FORBIDDEN", "다른 구성원 명의로 요청할 수 없습니다.")
        await family_service.get_family_member(body.requested_by)  # 없으면 NOT_FOUND
    request = await service.create_request(
        user_id=body.user_id, requested_by=body.requested_by, message=body.message
    )
    return DataResponse(data=_to_response(request))


@router.get("/users/{user_id}/photo-requests", response_model=DataResponse[list[PhotoRequestResponse]])
async def list_user_photo_requests(
    user_id: uuid.UUID,
    service: PhotoRequestService = Depends(_service),
    principal: Principal = Depends(require_principal),
) -> DataResponse[list[PhotoRequestResponse]]:
    """당사자(모바일 WU3, Device Token) 또는 가족(WF3에서 자기 요청 상태 확인)이 조회."""
    authorize_user_access(principal, user_id)
    requests = await service.list_requests_for_user(user_id)
    return DataResponse(data=[_to_response(r) for r in requests])


@router.post("/photo-requests/{request_id}/dismiss", response_model=DataResponse[PhotoRequestResponse])
async def dismiss_photo_request(
    request_id: uuid.UUID,
    service: PhotoRequestService = Depends(_service),
    principal: Principal = Depends(require_principal),
) -> DataResponse[PhotoRequestResponse]:
    """당사자가 "지금은 어렵다"며 요청을 닫는다 — pending 상태에서만 가능(이미
    fulfilled/dismissed면 CONFLICT). 충족(fulfilled)은 이 엔드포인트가 아니라
    photos 모듈의 업로드 완료 콜백이 자동으로 처리한다(photo_request_service.py
    fulfill_pending_for_user 참조)."""
    target = await service.get_request(request_id)
    authorize_user_access(principal, target.user_id)
    request = await service.dismiss_request(request_id)
    return DataResponse(data=_to_response(request))
