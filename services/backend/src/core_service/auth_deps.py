"""FastAPI 인증·인가 의존성의 조립 지점(composition root).

`core/auth.py`는 순수 로직만 둔다(토큰 검증·인가 규칙·조회 포트 Protocol). 그 포트를
실제 리포지토리(`family_members`/`devices`)로 구현하고 FastAPI `Depends` 함수로 엮는
일은 여기서 한다 — `main.py`/`core/model_registry.py`처럼 `modules`를 자유롭게 import하는
최상위 조립 모듈이라, import-linter가 `core/`는 `modules` 의존을 막지만 이 파일은 막지 않는다.

**라우터는 인증 관련 심볼을 전부 이 모듈에서 가져온다** (`core.auth`에서 직접 X).
"""

from __future__ import annotations

import hashlib
import uuid
from typing import Protocol

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
    "authorize_elder_data_read",
    "ConsentDirectory",
    "get_consent_directory",
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
# 동의 게이트 인가 (social_worker 제3자제공, decisions.md #54) — consent 모듈 의존이라
# core/auth.py(순수)가 아니라 여기(composition root)에 둔다. FamilyMemberDirectory와
# 동일하게 Protocol + 리포지토리 구현으로 분리해 순수 로직을 Fake로 단위 테스트한다.
# --------------------------------------------------------------------------- #
_SOCIAL_WORKER_READ_ROLES: frozenset[FamilyRole] = READ_ELDER_DATA_ROLES | {FamilyRole.SOCIAL_WORKER}


class ConsentDirectory(Protocol):
    async def has_third_party_access(self, user_id: uuid.UUID) -> bool: ...


class _ConsentDirectory:
    """`ConsentDirectory` 구현 — `consent_logs` 리포지토리 위임."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def has_third_party_access(self, user_id: uuid.UUID) -> bool:
        from core_service.modules.consent.domain.consent_log import ConsentType
        from core_service.modules.consent.infrastructure.consent_log_repository import (
            ConsentLogRepository,
        )

        logs = await ConsentLogRepository(self._session).list_by_user(user_id)
        return next(
            (log.granted for log in logs if log.consent_type == ConsentType.THIRD_PARTY_ACCESS), False
        )


def get_consent_directory(session: AsyncSession = Depends(get_db)) -> ConsentDirectory:
    return _ConsentDirectory(session)


async def authorize_elder_data_read(
    principal: Principal,
    target_user_id: uuid.UUID,
    consent_directory: ConsentDirectory,
    *,
    require_2fa: bool = True,
) -> None:
    """챕터·사진·대화·일정 등 어르신 데이터 **조회** 전용 — `authorize_user_access`에
    social_worker 게이트를 얹는다(decisions.md #54, 2026-09-12 사용자 결정).

    Q3: 가족·caregiver는 제26조 위탁범위 내 이용이라 기존과 동일하게 무조건 허용.
    복지사(social_worker)는 제17조 제3자제공으로 봐서, 어르신(또는 가족 대리)이
    `third_party_access` 동의를 준 경우에만 허용한다 — 이전의 전면 fail-closed
    (decisions.md #48)를 대체한다.
    """
    authorize_user_access(
        principal, target_user_id, allowed_roles=_SOCIAL_WORKER_READ_ROLES, require_2fa=require_2fa
    )

    if not isinstance(principal, AuthContext) or principal.is_admin:
        return
    membership = principal.membership_for(target_user_id)
    if membership is None or membership.role != FamilyRole.SOCIAL_WORKER:
        return  # family/caregiver는 위 authorize_user_access 통과로 충분

    if not await consent_directory.has_third_party_access(target_user_id):
        raise ApiError(
            "FORBIDDEN",
            "복지사 열람에는 어르신(또는 가족 대리)의 제3자 제공 동의가 필요합니다.",
        )


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
