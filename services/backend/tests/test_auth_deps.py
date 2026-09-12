"""auth_deps.py 유닛 테스트 — `authorize_elder_data_read`(decisions.md #54, Q3).

`core/auth.py`의 `authorize_user_access`는 순수(모듈 의존 금지)라 consent를 모른다.
social_worker의 `third_party_access` 동의 게이트는 composition root인 이 모듈에
있고, `ConsentDirectory`를 Fake로 갈아끼워 순수하게 테스트한다(HTTP·실 DB 없이).
"""

import uuid

import pytest

from core_service.auth_deps import ConsentDirectory, authorize_elder_data_read
from core_service.core.auth import AuthContext, DeviceIdentity, Membership
from core_service.core.errors import ApiError
from core_service.shared.domain_enums import FamilyRole


def _ctx(*memberships: Membership, is_2fa: bool = True) -> AuthContext:
    return AuthContext(subject="kc-sub-1", is_2fa=is_2fa, memberships=list(memberships))


def _member(user_id: uuid.UUID, role: FamilyRole) -> Membership:
    return Membership(family_member_id=uuid.uuid4(), user_id=user_id, role=role, two_factor_enabled=True)


class _FakeConsentDirectory:
    def __init__(self, has_access: bool):
        self._has_access = has_access
        self.calls: list[uuid.UUID] = []

    async def has_third_party_access(self, user_id: uuid.UUID) -> bool:
        self.calls.append(user_id)
        return self._has_access


def _fake(has_access: bool) -> ConsentDirectory:
    return _FakeConsentDirectory(has_access)  # type: ignore[return-value]


async def test_family_allowed_without_consent_check() -> None:
    """가족(위탁범위 내 이용)은 third_party_access 동의와 무관하게 통과 — 동의
    조회 자체가 일어나지 않아야 한다(불필요한 DB 왕복 방지)."""
    elder = uuid.uuid4()
    ctx = _ctx(_member(elder, FamilyRole.FAMILY))
    directory = _FakeConsentDirectory(has_access=False)

    await authorize_elder_data_read(ctx, elder, directory)  # type: ignore[arg-type]

    assert directory.calls == []


async def test_caregiver_allowed_without_consent_check() -> None:
    elder = uuid.uuid4()
    ctx = _ctx(_member(elder, FamilyRole.CAREGIVER))
    directory = _FakeConsentDirectory(has_access=False)

    await authorize_elder_data_read(ctx, elder, directory)  # type: ignore[arg-type]

    assert directory.calls == []


async def test_social_worker_denied_without_consent() -> None:
    elder = uuid.uuid4()
    ctx = _ctx(_member(elder, FamilyRole.SOCIAL_WORKER))
    directory = _FakeConsentDirectory(has_access=False)

    with pytest.raises(ApiError, match="제3자 제공 동의"):
        await authorize_elder_data_read(ctx, elder, directory)  # type: ignore[arg-type]

    assert directory.calls == [elder]


async def test_social_worker_allowed_with_consent() -> None:
    elder = uuid.uuid4()
    ctx = _ctx(_member(elder, FamilyRole.SOCIAL_WORKER))
    directory = _FakeConsentDirectory(has_access=True)

    await authorize_elder_data_read(ctx, elder, directory)  # type: ignore[arg-type]

    assert directory.calls == [elder]


async def test_admin_bypasses_consent_check() -> None:
    elder = uuid.uuid4()
    ctx = _ctx(_member(uuid.uuid4(), FamilyRole.ADMIN))
    directory = _FakeConsentDirectory(has_access=False)

    await authorize_elder_data_read(ctx, elder, directory)  # type: ignore[arg-type]

    assert directory.calls == []


async def test_device_identity_bypasses_consent_check() -> None:
    """기기(어르신 본인)는 항상 자기 자신 데이터라 social_worker 분기 자체를 안 탄다."""
    elder = uuid.uuid4()
    device = DeviceIdentity(device_id=uuid.uuid4(), user_id=elder)
    directory = _FakeConsentDirectory(has_access=False)

    await authorize_elder_data_read(device, elder, directory)  # type: ignore[arg-type]

    assert directory.calls == []


async def test_social_worker_without_membership_still_forbidden_by_base_check() -> None:
    """연결 안 된 어르신은 authorize_user_access 단계에서 이미 막힌다 —
    consent 조회까지 가지 않는다."""
    elder = uuid.uuid4()
    ctx = _ctx(_member(uuid.uuid4(), FamilyRole.SOCIAL_WORKER))
    directory = _FakeConsentDirectory(has_access=True)

    with pytest.raises(ApiError, match="연결"):
        await authorize_elder_data_read(ctx, elder, directory)  # type: ignore[arg-type]

    assert directory.calls == []
