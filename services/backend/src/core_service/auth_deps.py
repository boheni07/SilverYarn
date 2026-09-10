"""FastAPI 인증·인가 의존성의 조립 지점(composition root).

`core/auth.py`는 순수 로직만 둔다(토큰 검증·인가 규칙·조회 포트 Protocol). 그 포트를
실제 리포지토리(`family_members`/`devices`)로 구현하고 FastAPI `Depends` 함수로 엮는
일은 여기서 한다 — `main.py`/`core/model_registry.py`처럼 `modules`를 자유롭게 import하는
최상위 조립 모듈이라, import-linter가 `core/`는 `modules` 의존을 막지만 이 파일은 막지 않는다.

**라우터는 인증 관련 심볼을 전부 이 모듈에서 가져온다** (`core.auth`에서 직접 X).
"""

from __future__ import annotations

import hashlib

from fastapi import Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from core_service.core.auth import (
    READ_ELDER_DATA_ROLES,
    WRITE_ELDER_DATA_ROLES,
    AuthContext,
    DeviceIdentity,
    DeviceTokenDirectory,
    FamilyMemberDirectory,
    Membership,
    Principal,
    VerifiedSubject,
    authorize_own_family_member,
    authorize_user_access,
    build_family_context,
    require_verified_subject,
)
from core_service.core.db import get_db
from core_service.core.errors import ApiError
from core_service.shared.domain_enums import FamilyRole

# core.auth의 순수 심볼을 라우터가 이 모듈 하나에서 가져올 수 있게 재노출한다.
__all__ = [
    "AuthContext",
    "DeviceIdentity",
    "Membership",
    "Principal",
    "VerifiedSubject",
    "READ_ELDER_DATA_ROLES",
    "WRITE_ELDER_DATA_ROLES",
    "authorize_own_family_member",
    "authorize_user_access",
    "require_verified_subject",
    "require_family",
    "require_auth",
    "require_device",
    "require_device_token",
    "require_principal",
    "require_auth_or_device_token",
    "require_roles",
]


# --------------------------------------------------------------------------- #
# 조회 포트 구현 (Protocol → 리포지토리)
# --------------------------------------------------------------------------- #
class _FamilyMemberDirectory:
    """`core.auth.FamilyMemberDirectory` 구현 — `family_members` 리포지토리 위임."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def memberships_for_subject(self, subject: str) -> list[Membership]:
        from core_service.modules.family_members.infrastructure.family_member_repository import (
            FamilyMemberRepository,
        )

        members = await FamilyMemberRepository(self._session).list_by_keycloak_sub(subject)
        return [
            Membership(
                family_member_id=m.id,
                user_id=m.user_id,
                role=m.role,
                two_factor_enabled=m.two_factor_enabled,
            )
            for m in members
        ]


class _DeviceTokenDirectory:
    """`core.auth.DeviceTokenDirectory` 구현 — `device_credentials` 리포지토리 위임."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def resolve_active(self, token_hash: str) -> DeviceIdentity | None:
        from core_service.modules.devices.infrastructure.device_credential_repository import (
            DeviceCredentialRepository,
        )

        return await DeviceCredentialRepository(self._session).resolve_active(token_hash)


def get_family_directory(session: AsyncSession = Depends(get_db)) -> FamilyMemberDirectory:
    return _FamilyMemberDirectory(session)


def get_device_directory(session: AsyncSession = Depends(get_db)) -> DeviceTokenDirectory:
    return _DeviceTokenDirectory(session)


# --------------------------------------------------------------------------- #
# principal 해석 의존성
# --------------------------------------------------------------------------- #
async def require_family(
    request: Request,
    authorization: str | None = Header(default=None),
    directory: FamilyMemberDirectory = Depends(get_family_directory),
) -> AuthContext:
    """Keycloak 액세스 토큰 검증 → `family_members`(keycloak_sub) 조회 → AuthContext.

    인증은 됐으나 어떤 어르신에도 연결되지 않은 계정(provisioning 전)은 403.
    """
    verified = await require_verified_subject(authorization)
    memberships = await directory.memberships_for_subject(verified.subject)
    ctx = build_family_context(verified, memberships)
    request.state.actor_kind = "family_member"
    request.state.actor_subject = verified.subject
    return ctx


# 기존 라우터가 `Depends(require_auth)`를 광범위하게 쓰므로 별칭을 유지한다.
require_auth = require_family


async def require_device(
    request: Request,
    x_device_token: str | None = Header(default=None),
    directory: DeviceTokenDirectory = Depends(get_device_directory),
) -> DeviceIdentity:
    """`X-Device-Token`을 SHA-256 해시로 `device_credentials`에서 조회(폐기되지 않은 것)."""
    if not x_device_token:
        raise ApiError("UNAUTHORIZED", "기기 토큰이 필요합니다.")

    token_hash = hashlib.sha256(x_device_token.encode()).hexdigest()
    identity = await directory.resolve_active(token_hash)
    if identity is None:
        raise ApiError("UNAUTHORIZED", "유효하지 않거나 폐기된 기기 토큰입니다.")

    request.state.actor_kind = "device"
    request.state.actor_subject = str(identity.device_id)
    return identity


# 별칭 — 반환 타입이 str에서 DeviceIdentity로 바뀐 것에 주의(호출부 갱신 완료).
require_device_token = require_device


async def require_principal(
    request: Request,
    authorization: str | None = Header(default=None),
    x_device_token: str | None = Header(default=None),
    family_directory: FamilyMemberDirectory = Depends(get_family_directory),
    device_directory: DeviceTokenDirectory = Depends(get_device_directory),
) -> Principal:
    """가족 토큰 또는 Device Token 중 하나 (design.md §4.2 photos/consent 등)."""
    if authorization:
        return await require_family(request, authorization, family_directory)
    if x_device_token:
        return await require_device(request, x_device_token, device_directory)
    raise ApiError("UNAUTHORIZED", "인증 토큰 또는 기기 토큰이 필요합니다.")


require_auth_or_device_token = require_principal


def require_roles(*roles: FamilyRole, require_2fa: bool = True):  # noqa: ANN201 (FastAPI 의존성 팩토리)
    """어르신에 종속되지 않는 엔드포인트(관리자 콘솔 등)용 — 토큰 소유자가 어딘가에서
    지정 역할 중 하나를 갖는지만 본다."""

    async def _dep(ctx: AuthContext = Depends(require_family)) -> AuthContext:
        if not (ctx.roles & set(roles)):
            raise ApiError("FORBIDDEN", "이 엔드포인트에 필요한 역할이 없습니다.")
        if require_2fa and not ctx.is_2fa:
            raise ApiError("FORBIDDEN", "이 작업에는 2단계 인증이 필요합니다.")
        return ctx

    return _dep
