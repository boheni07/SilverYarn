"""인증·인가 — 순수 로직만 (Keycloak SSO decisions.md #17 + Device Token decisions.md #47).

원본 프로세스흐름도 §4.1: 모든 요청(배치 동기화 / 웹 콘솔 API)은 게이트웨이에서
Keycloak SSO 인증/인가를 거친다. 웹 콘솔은 사람(가족·복지사·관리자), 모바일 동기화는
기기가 주체다.

## 이 모듈의 범위 (순수 — `core_service.modules`에 의존하지 않는다)
- `KeycloakVerifier` — JWKS 캐시 + RS256 서명·iss·aud·exp 검증
- `require_verified_subject` — Bearer 토큰만 검증(연결 여부는 안 봄). 초대 수락 부트스트랩용
- `authorize_user_access` / `authorize_own_family_member` — 이미 해석된 principal에 대한 인가 규칙
- `FamilyMemberDirectory` / `DeviceTokenDirectory` — principal 해석에 필요한 조회 포트(Protocol)

## principal 해석(=DB 조회)이 필요한 FastAPI 의존성
`require_family` / `require_device` / `require_principal` / `require_roles`는
`core_service/auth_deps.py`(조립 지점, 리포지토리와 엮는 곳)에 있다. 라우터는 인증
심볼을 전부 거기서 가져온다.

## 실패 모드 (fail closed)
`AUTH_ISSUER_URL`이 비어 있으면 토큰 검증이 처음 호출될 때 RuntimeError. 앱/워커
기동과 CI(HTTP 미경유 단위 테스트)에는 영향 없다.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Protocol

import httpx
from fastapi import Header
from jose import JWTError, jwt

from core_service.core.config import Settings, get_settings
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
# 조회 포트 (auth_deps.py가 리포지토리로 구현)
# --------------------------------------------------------------------------- #
class FamilyMemberDirectory(Protocol):
    """Keycloak `sub` → 이 계정에 연결된 `family_members` 행(들). `require_family`가 쓴다."""

    async def memberships_for_subject(self, subject: str) -> list[Membership]: ...


class DeviceTokenDirectory(Protocol):
    """Device Token 해시 → 그 기기의 identity(폐기되지 않은 것). `require_device`가 쓴다."""

    async def resolve_active(self, token_hash: str) -> DeviceIdentity | None: ...


# --------------------------------------------------------------------------- #
# 토큰 검증 의존성 (순수 — DB 조회 없음)
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
    # 토큰 유무를 먼저 본다 — 없으면 401(verifier를 만들지도 않는다). verifier 생성이
    # AUTH_ISSUER_URL 미설정 시 RuntimeError라, 순서가 반대면 무인증 요청이 500이 된다.
    token = _bearer_token(authorization)
    claims = await get_verifier().verify(token)
    subject = str(claims.get("sub", ""))
    if not subject:
        raise ApiError("UNAUTHORIZED", "토큰에 sub claim이 없습니다.")
    return VerifiedSubject(subject=subject, is_2fa=_is_2fa(claims))


def build_family_context(verified: VerifiedSubject, memberships: list[Membership]) -> AuthContext:
    """검증된 토큰 + 조회된 membership 목록 → AuthContext. 연결이 없으면 403.

    `require_family`(auth_deps.py)가 `FamilyMemberDirectory` 조회 결과를 넘겨 호출한다 —
    조회 방식(리포지토리)과 규칙(연결 없으면 403)을 분리해 규칙만 여기서 순수하게 검증한다.
    """
    if not memberships:
        raise ApiError(
            "FORBIDDEN", "이 계정은 아직 어떤 어르신 계정에도 연결되지 않았습니다(초대 수락 필요)."
        )
    return AuthContext(subject=verified.subject, is_2fa=verified.is_2fa, memberships=list(memberships))


# --------------------------------------------------------------------------- #
# 인가 헬퍼 (이미 해석된 principal에 대한 규칙 — 순수)
# --------------------------------------------------------------------------- #
# design.md §7.1 RBAC 매트릭스 — 어르신 데이터(챕터·사진·대화·일정·동의) 조회 허용 역할.
#
# ⚠️ social_worker(복지사)는 여기 없다 — family/caregiver/admin은 무조건 허용이지만,
# 복지사는 decisions.md #54(2026-09-12 사용자 결정, Q3)로 "제17조 제3자제공"으로
# 확정돼 **전용 동의(`third_party_access`)가 있을 때만** 허용해야 한다. 그 동의
# 여부는 DB 조회가 필요해 이 순수 함수(모듈 의존 금지)로는 표현할 수 없다 — 실제
# 게이트는 `auth_deps.authorize_elder_data_read()`(composition root)에 있다.
# 이 상수를 직접 쓰는 호출부는 그 함수를 거치지 않으므로 social_worker가 자동으로
# 막힌다(과거 fail-closed, decisions.md #48 — 이제 위 함수로 조건부 허용 대체).
READ_ELDER_DATA_ROLES: frozenset[FamilyRole] = frozenset(
    {FamilyRole.FAMILY, FamilyRole.CAREGIVER, FamilyRole.ADMIN}
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
