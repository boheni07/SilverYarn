"""`GET /me` — 로그인 세션(Keycloak 토큰)만으로 "이 계정이 어느 어르신(들)에
연결돼 있는지"를 알려주는 자기참조 엔드포인트.

**왜 필요한가**: `require_auth`가 매 요청마다 토큰→`family_members`를 조회해
`AuthContext.memberships`를 만들지만, 그 결과를 클라이언트에게 돌려주는 엔드포인트가
지금까지 없었다 — 그래서 웹 콘솔(apps/web)의 모든 화면이 "어느 어르신 화면인지"를
알아낼 방법이 없어 `?userId=` 쿼리스트링을 사람이 직접 입력해야 했다(screen-definitions.md
§0.3 "임시방편"). 이 엔드포인트는 새 조회 로직이 전혀 필요 없다 — `require_auth`가 이미
계산해 둔 `AuthContext.memberships`를 그대로 직렬화할 뿐이다.
"""

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from core_service.auth_deps import AuthContext, require_auth
from core_service.shared.schemas import DataResponse

router = APIRouter(tags=["auth"])


class MembershipResponse(BaseModel):
    family_member_id: uuid.UUID
    user_id: uuid.UUID
    role: str
    two_factor_enabled: bool
    org_id: uuid.UUID | None = None


class MeResponse(BaseModel):
    memberships: list[MembershipResponse]


@router.get("/me", response_model=DataResponse[MeResponse])
async def get_me(ctx: AuthContext = Depends(require_auth)) -> DataResponse[MeResponse]:
    return DataResponse(
        data=MeResponse(
            memberships=[
                MembershipResponse(
                    family_member_id=m.family_member_id,
                    user_id=m.user_id,
                    role=m.role.value,
                    two_factor_enabled=m.two_factor_enabled,
                    org_id=m.org_id,
                )
                for m in ctx.memberships
            ]
        )
    )
