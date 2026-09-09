"""인증·인가 — Keycloak SSO(decisions.md #17) + Device Token(decisions.md #47).

원본 프로세스흐름도 §4.1: 모든 요청(배치 동기화 / 웹 콘솔 API)은 게이트웨이에서
Keycloak SSO 인증/인가를 거친다. 웹 콘솔은 사람(가족·복지사·관리자), 모바일 동기화는
기기가 주체다.

## 구성요소
- `KeycloakVerifier` — JWKS 캐시 + RS256 서명·iss·aud·exp 검증
- `require_family` — Bearer 토큰 검증 → `sub`로 `family_members` 조회 → `AuthContext`
- `require_device` — `X-Device-Token` → SHA-256 해시로 `device_credentials` 조회 → `DeviceIdentity`
- `require_principal` — 가족 토큰 **또는** Device Token (photos/consent 등)
- `authorize_user_access` — 대상 어르신(`user_id`)에 대한 접근 인가(IDOR 방지, RBAC 매트릭스)
- `require_roles(...)` — 어르신에 종속되지 않는 관리자 전용 엔드포인트용

## 실패 모드 (fail closed)
`AUTH_ISSUER_URL`이 비어 있으면 `require_family`가 처음 호출될 때 RuntimeError. 앱/워커
기동과 CI(Fake repository 단위 테스트, HTTP 미경유)에는 영향 없다.
"""

from __future__ import annotations

import hashlib
import time
import uuid
from dataclasses import dataclass, field

import httpx
from fastapi import Depends, Header, Request
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from core_service.core.config import Settings, get_settings
from core_service.core.db import get_db
from core_service.core.errors import ApiError
from core_service.shared.domain_enums import FamilyRole

_ADMIN_ROLE = FamilyRole.ADMIN


# --------------------------------------------------------------------------- #
# Keycloak 토큰 검증
# --------------------------------------------------------------------------- #
class KeycloakVerifier:
    """JWKS를 캐시하고 RS256 액세스 토큰을 검증한다. 프로세스 싱글턴."""

    def __init__(self, settings: Settings):
        if not settings.auth_issuer_url:
            raise RuntimeError(
                "AUTH_ISSUER_URL이 비어 있습니다 — Keycloak realm 발급자 URL을 시크릿 매니저/"
                ".env로 주입해야 웹 콘솔 인증이 동작합니다(CONVENTIONS.md §4)."
            )
        self._settings = settings
        self._jwks: dict | None = None
        self._fetched_at = 0.0

    async def _get_jwks(self) -> dict:
        now = time.monotonic()
        if self._jwks is None or now - self._fetched_at > self._settings.auth_jwks_cache_seconds:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(self._settings.resolved_jwks_url)
                resp.raise_for_status()
                self._jwks = resp.json()
                self._fetched_at = now
        return self._jwks

    async def verify(self, token: str) -> dict:
        try:
            jwks = await self._get_jwks()
        except httpx.HTTPError as exc:
            raise ApiError("INTERNAL_ERROR", "인증 서버(JWKS)에 연결할 수 없습니다.") from exc
        try:
            return jwt.decode(
                token,
                jwks,
                algorithms=["RS256"],
                audience=self._settings.resolved_audience,
                issuer=self._settings.auth_issuer_url,
                options={"require_exp": True},
            )
        except JWTError as exc:
            raise ApiError("UNAUTHORIZED", f"토큰 검증 실패: {exc}") from exc


_verifier: KeycloakVerifier | None = None


def get_verifier() -> KeycloakVerifier:
    global _verifier
    if _verifier is None:
        _verifier = KeycloakVerifier(get_settings())
    return _verifier


def _is_2fa(claims: dict) -> bool:
    """토큰이 step-up(2FA) 인증을 반영하는지. Keycloak 인증흐름 설정에 따라 `amr`에
    mfa/otp 등이 담긴다(AUTH_2FA_AMR_VALUES로 조정)."""
    amr = claims.get("amr") or []
    if isinstance(amr, str):
        amr = [amr]
    return bool(set(amr) & get_settings().auth_2fa_amr_values)


# --------------------------------------------------------------------------- #
# Principal 타입
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Membership:
    family_member_id: uuid.UUID
    user_id: uuid.UUID  # 이 구성원이 속한 어르신
    role: FamilyRole
    two_factor_enabled: bool


@dataclass
class AuthContext:
    """웹 콘솔 사용자(가족/복지사/관리자) principal — 하나의 Keycloak 계정이
    여러 어르신에 연결될 수 있어 `memberships`는 리스트다."""

    subject: str
    is_2fa: bool
    memberships: list[Membership] = field(default_factory=list)

    @property
    def roles(self) -> set[FamilyRole]:
        return {m.role for m in self.memberships}

    @property
    def is_admin(self) -> bool:
        return _ADMIN_ROLE in self.roles

    def membership_for(self, user_id: uuid.UUID) -> Membership | None:
        return next((m for m in self.memberships if m.user_id == user_id), None)


@dataclass(frozen=True)
class DeviceIdentity:
    """모바일 동기화 principal — 기기와 그 기기가 속한 어르신."""

    device_id: uuid.UUID
    user_id: uuid.UUID


Principal = AuthContext | DeviceIdentity


# --------------------------------------------------------------------------- #
# 의존성
# --------------------------------------------------------------------------- #
def _bearer_token(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise ApiError("UNAUTHORIZED", "Bearer 토큰이 필요합니다.")
    return authorization[7:].strip()


@dataclass(frozen=True)
class VerifiedSubject:
    """Keycloak 토큰 서명·클레임만 검증한 결과 — family_members 연결 여부는 보지 않는다."""

    subject: str
    is_2fa: bool


async def require_verified_subject(
    authorization: str | None = Header(default=None),
) -> VerifiedSubject:
    """토큰만 검증하고 `sub`를 돌려준다. '연결을 만드는' 부트스트랩 엔드포인트
    (초대 수락 — 아직 어떤 family_member에도 매핑 안 된 계정)용."""
    claims = await get_verifier().verify(_bearer_token(authorization))
    subject = str(claims.get("sub", ""))
    if not subject:
        raise ApiError("UNAUTHORIZED", "토큰에 sub claim이 없습니다.")
    return VerifiedSubject(subject=subject, is_2fa=_is_2fa(claims))


async def require_family(
    request: Request,
    authorization: str | None = Header(default=None),
    session: AsyncSession = Depends(get_db),
) -> AuthContext:
    """Keycloak 액세스 토큰 검증 → `family_members`(keycloak_sub) 조회 → AuthContext.

    인증은 됐으나 어떤 어르신에도 연결되지 않은 계정(provisioning 전)은 403.
    """
    verified = await require_verified_subject(authorization)
    subject = verified.subject
    claims_is_2fa = verified.is_2fa

    from core_service.modules.family_members.infrastructure.family_member_repository import (
        FamilyMemberRepository,
    )

    members = await FamilyMemberRepository(session).list_by_keycloak_sub(subject)
    if not members:
        raise ApiError(
            "FORBIDDEN", "이 계정은 아직 어떤 어르신 계정에도 연결되지 않았습니다(초대 수락 필요)."
        )

    ctx = AuthContext(
        subject=subject,
        is_2fa=claims_is_2fa,
        memberships=[
            Membership(
                family_member_id=m.id,
                user_id=m.user_id,
                role=m.role,
                two_factor_enabled=m.two_factor_enabled,
            )
            for m in members
        ],
    )
    request.state.actor_kind = "family_member"
    request.state.actor_subject = subject
    return ctx


# 기존 라우터가 `Depends(require_auth)`를 광범위하게 쓰므로 별칭을 유지한다.
require_auth = require_family


async def require_device(
    request: Request,
    x_device_token: str | None = Header(default=None),
    session: AsyncSession = Depends(get_db),
) -> DeviceIdentity:
    """`X-Device-Token`을 SHA-256 해시로 `device_credentials`에서 조회(폐기되지 않은 것)."""
    if not x_device_token:
        raise ApiError("UNAUTHORIZED", "기기 토큰이 필요합니다.")

    from core_service.modules.devices.infrastructure.device_credential_repository import (
        DeviceCredentialRepository,
    )

    token_hash = hashlib.sha256(x_device_token.encode()).hexdigest()
    identity = await DeviceCredentialRepository(session).resolve_active(token_hash)
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
    session: AsyncSession = Depends(get_db),
) -> Principal:
    """가족 토큰 또는 Device Token 중 하나 (design.md §4.2 photos/consent 등)."""
    if authorization:
        return await require_family(request, authorization, session)
    if x_device_token:
        return await require_device(request, x_device_token, session)
    raise ApiError("UNAUTHORIZED", "인증 토큰 또는 기기 토큰이 필요합니다.")


require_auth_or_device_token = require_principal


# --------------------------------------------------------------------------- #
# 인가 헬퍼
# --------------------------------------------------------------------------- #
# design.md §7.1 RBAC 매트릭스 — 어르신 데이터(챕터·사진·대화·일정·동의) 조회 기본 허용 역할.
READ_ELDER_DATA_ROLES: frozenset[FamilyRole] = frozenset(
    {FamilyRole.FAMILY, FamilyRole.CAREGIVER, FamilyRole.SOCIAL_WORKER, FamilyRole.ADMIN}
)
# 감수·설정 변경 등 쓰기 작업 — 가족/관리자만.
WRITE_ELDER_DATA_ROLES: frozenset[FamilyRole] = frozenset({FamilyRole.FAMILY, FamilyRole.ADMIN})


def authorize_user_access(
    principal: Principal,
    target_user_id: uuid.UUID,
    *,
    allowed_roles: frozenset[FamilyRole] = READ_ELDER_DATA_ROLES,
    require_2fa: bool = True,
) -> None:
    """`target_user_id`(어르신)의 데이터에 접근할 권한이 있는지 검증. 없으면 403.

    - Device: 자기 자신이 속한 어르신만.
    - 가족류: admin은 전체 허용. 그 외는 해당 어르신에 대한 membership이 있고 role이
      `allowed_roles`에 들며, `require_2fa`면 토큰이 2FA를 반영해야 한다
      (기획서 6장 "웹 콘솔 접근 시 2단계 인증").
    """
    if isinstance(principal, DeviceIdentity):
        if principal.user_id != target_user_id:
            raise ApiError("FORBIDDEN", "이 기기는 해당 어르신의 데이터에 접근할 수 없습니다.")
        return

    if principal.is_admin:
        return

    membership = principal.membership_for(target_user_id)
    if membership is None:
        raise ApiError("FORBIDDEN", "이 어르신 계정에 연결돼 있지 않습니다.")
    if membership.role not in allowed_roles:
        raise ApiError("FORBIDDEN", f"'{membership.role.value}' 역할은 이 작업을 수행할 수 없습니다.")
    if require_2fa and not principal.is_2fa:
        raise ApiError("FORBIDDEN", "이 작업에는 2단계 인증이 필요합니다.")


def authorize_own_family_member(
    ctx: AuthContext,
    family_member_id: uuid.UUID,
    *,
    require_2fa: bool = True,
) -> None:
    """`family_member_id`가 호출자 **본인의** 구성원 행인지 검증(admin은 우회).

    design.md §7.1 "알림 수신 설정 변경 = 본인 것만" 같은, 어르신 데이터가 아니라
    구성원 자신의 설정을 다루는 엔드포인트용.
    """
    if ctx.is_admin:
        return
    if family_member_id not in {m.family_member_id for m in ctx.memberships}:
        raise ApiError("FORBIDDEN", "본인의 구성원 설정만 변경할 수 있습니다.")
    if require_2fa and not ctx.is_2fa:
        raise ApiError("FORBIDDEN", "이 작업에는 2단계 인증이 필요합니다.")


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
