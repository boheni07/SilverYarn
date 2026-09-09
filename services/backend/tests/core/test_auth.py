"""core/auth.py 유닛 테스트 — 인가 규칙(authorize_user_access)과 토큰 검증.

라우터(HTTP) 레벨 인증 흐름은 로컬 e2e(수기, Keycloak realm 필요)로 검증한다 —
여기서는 순수 로직만 본다.
"""

import time
import uuid

import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from jose import jwt

from core_service.core.auth import (
    AuthContext,
    DeviceIdentity,
    KeycloakVerifier,
    Membership,
    _is_2fa,
    authorize_user_access,
)
from core_service.core.config import Settings
from core_service.core.errors import ApiError
from core_service.shared.domain_enums import FamilyRole


def _ctx(*memberships: Membership, is_2fa: bool = True) -> AuthContext:
    return AuthContext(subject="kc-sub-1", is_2fa=is_2fa, memberships=list(memberships))


def _member(user_id: uuid.UUID, role: FamilyRole) -> Membership:
    return Membership(family_member_id=uuid.uuid4(), user_id=user_id, role=role, two_factor_enabled=True)


# --- authorize_user_access ---------------------------------------------------
def test_device_only_its_own_elder() -> None:
    elder = uuid.uuid4()
    authorize_user_access(DeviceIdentity(device_id=uuid.uuid4(), user_id=elder), elder)
    with pytest.raises(ApiError) as exc:
        authorize_user_access(DeviceIdentity(device_id=uuid.uuid4(), user_id=uuid.uuid4()), elder)
    assert exc.value.code == "FORBIDDEN"


def test_admin_bypasses_membership_and_2fa_role_checks() -> None:
    admin_ctx = _ctx(_member(uuid.uuid4(), FamilyRole.ADMIN), is_2fa=True)
    authorize_user_access(admin_ctx, uuid.uuid4())  # 연결 안 된 어르신도 통과


def test_family_needs_membership_for_that_elder() -> None:
    elder_a, elder_b = uuid.uuid4(), uuid.uuid4()
    ctx = _ctx(_member(elder_a, FamilyRole.FAMILY))
    authorize_user_access(ctx, elder_a)
    with pytest.raises(ApiError, match="연결"):
        authorize_user_access(ctx, elder_b)


def test_role_not_in_allowed_set_is_forbidden() -> None:
    elder = uuid.uuid4()
    ctx = _ctx(_member(elder, FamilyRole.SOCIAL_WORKER))
    # 읽기는 허용
    authorize_user_access(ctx, elder)
    # 쓰기(family/admin만)는 금지
    from core_service.core.auth import WRITE_ELDER_DATA_ROLES

    with pytest.raises(ApiError, match="역할"):
        authorize_user_access(ctx, elder, allowed_roles=WRITE_ELDER_DATA_ROLES)


def test_missing_2fa_is_forbidden_when_required() -> None:
    elder = uuid.uuid4()
    ctx = _ctx(_member(elder, FamilyRole.FAMILY), is_2fa=False)
    with pytest.raises(ApiError, match="2단계 인증"):
        authorize_user_access(ctx, elder)
    # require_2fa=False면 통과
    authorize_user_access(ctx, elder, require_2fa=False)


# --- _is_2fa ---------------------------------------------------------------
@pytest.mark.parametrize(
    ("claims", "expected"),
    [
        ({"amr": ["pwd", "mfa"]}, True),
        ({"amr": "otp"}, True),
        ({"amr": ["pwd"]}, False),
        ({}, False),
    ],
)
def test_is_2fa(claims: dict, expected: bool) -> None:
    assert _is_2fa(claims) is expected


# --- KeycloakVerifier (JWKS 없이 로컬 키로) --------------------------------
@pytest.fixture
def verifier_and_key() -> tuple[KeycloakVerifier, rsa.RSAPrivateKey]:
    settings = Settings(
        _env_file=None,  # type: ignore[call-arg]
        AUTH_ISSUER_URL="https://kc.example/realms/silveryarn",
        AUTH_CLIENT_ID="silveryarn-backend",
    )
    verifier = KeycloakVerifier(settings)
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    numbers = private_key.public_key().public_numbers()

    def _b64(n: int) -> str:
        import base64

        raw = n.to_bytes((n.bit_length() + 7) // 8, "big")
        return base64.urlsafe_b64encode(raw).decode().rstrip("=")

    jwk = {
        "kty": "RSA",
        "kid": "test-key",
        "use": "sig",
        "alg": "RS256",
        "n": _b64(numbers.n),
        "e": _b64(numbers.e),
    }
    verifier._jwks = {"keys": [jwk]}  # noqa: SLF001 — fetch 우회
    verifier._fetched_at = time.monotonic()  # noqa: SLF001
    return verifier, private_key


def _pem(key: rsa.RSAPrivateKey) -> str:
    from cryptography.hazmat.primitives import serialization

    return key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()


async def test_verifier_accepts_valid_token(
    verifier_and_key: tuple[KeycloakVerifier, rsa.RSAPrivateKey],
) -> None:
    verifier, key = verifier_and_key
    token = jwt.encode(
        {
            "sub": "user-123",
            "iss": "https://kc.example/realms/silveryarn",
            "aud": "silveryarn-backend",
            "exp": int(time.time()) + 300,
            "amr": ["mfa"],
        },
        _pem(key),
        algorithm="RS256",
        headers={"kid": "test-key"},
    )
    claims = await verifier.verify(token)
    assert claims["sub"] == "user-123"


async def test_verifier_rejects_wrong_audience(
    verifier_and_key: tuple[KeycloakVerifier, rsa.RSAPrivateKey],
) -> None:
    verifier, key = verifier_and_key
    token = jwt.encode(
        {
            "sub": "user-123",
            "iss": "https://kc.example/realms/silveryarn",
            "aud": "some-other-client",
            "exp": int(time.time()) + 300,
        },
        _pem(key),
        algorithm="RS256",
        headers={"kid": "test-key"},
    )
    with pytest.raises(ApiError) as exc:
        await verifier.verify(token)
    assert exc.value.code == "UNAUTHORIZED"
