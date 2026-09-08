"""Keycloak SSO 인증 — decisions.md #17 확정, 원본 프로세스흐름도 §4.1.

⚠️ 스텁 상태: 토큰 서명 검증(JWKS)·2FA 체크는 미구현. 인프라(Keycloak realm) 준비 후
실 검증 로직을 채운다. 현재는 각 모듈 라우터가 의존성 주입 지점만 갖도록 시그니처를
확정해 두는 것이 목적.
"""

from dataclasses import dataclass

from fastapi import Header

from core_service.core.errors import ApiError


@dataclass
class AuthContext:
    """인증된 요청의 컨텍스트. Keycloak 토큰 claim에서 채워질 예정."""

    subject: str
    roles: list[str]


async def require_auth(authorization: str | None = Header(default=None)) -> AuthContext:
    """FastAPI Depends — 라우터에서 `ctx: AuthContext = Depends(require_auth)`로 사용.

    TODO(Do 단계): Keycloak JWKS로 서명 검증, family_members.role 매핑, 2FA 확인.
    """
    if not authorization:
        raise ApiError("UNAUTHORIZED", "인증 토큰이 필요합니다.")
    # 스텁: 검증 없이 통과 — 실 배포 전 반드시 교체
    return AuthContext(subject="stub-subject", roles=["family"])


async def require_device_token(x_device_token: str | None = Header(default=None)) -> str:
    """모바일 동기화 엔드포인트용 Device Token 검증 (sync-contract.md).

    TODO(Do 단계): device_credentials(erd.md §11 확장 후보, 결정 대기) 도입 시 실 검증.
    """
    if not x_device_token:
        raise ApiError("UNAUTHORIZED", "기기 토큰이 필요합니다.")
    return x_device_token


async def require_auth_or_device_token(
    authorization: str | None = Header(default=None),
    x_device_token: str | None = Header(default=None),
) -> AuthContext | str:
    """ "2FA + Role(family) 또는 Device Token" 인가(design.md §4.2 photos/upload-url,
    photos/{id}/complete) — 가족이 웹콘솔에서 사진을 올릴 수도, 어르신 모바일 기기가
    회고 중 촬영한 사진을 직접 올릴 수도 있어 둘 중 하나만 있으면 통과시킨다.
    """
    if authorization:
        return await require_auth(authorization)
    if x_device_token:
        return await require_device_token(x_device_token)
    raise ApiError("UNAUTHORIZED", "인증 토큰 또는 기기 토큰이 필요합니다.")
