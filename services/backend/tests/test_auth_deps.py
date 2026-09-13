"""auth_deps.py 유닛 테스트 — `authorize_elder_data_read`(decisions.md #54, #59).

`core/auth.py`의 `authorize_user_access`는 순수(모듈 의존 금지)라 consent·org를
모른다. social_worker의 `third_party_access` 동의 게이트(#54)와 B2G 시설 테넌시
안전망(#59)은 composition root인 이 모듈에 있고, `ConsentDirectory`/`UserDirectory`를
Fake로 갈아끼워 순수하게 테스트한다(HTTP·실 DB 없이).
"""

import uuid

import pytest

from core_service.auth_deps import ElderAccessContext, authorize_elder_data_read
from core_service.core.auth import AuthContext, DeviceIdentity, Membership
from core_service.core.errors import ApiError
from core_service.shared.domain_enums import FamilyRole


def _ctx(*memberships: Membership, is_2fa: bool = True) -> AuthContext:
    return AuthContext(subject="kc-sub-1", is_2fa=is_2fa, memberships=list(memberships))


def _member(user_id: uuid.UUID, role: FamilyRole, org_id: uuid.UUID | None = None) -> Membership:
    return Membership(
        family_member_id=uuid.uuid4(),
        user_id=user_id,
        role=role,
        two_factor_enabled=True,
        org_id=org_id,
    )


class _FakeConsentDirectory:
    def __init__(self, has_access: bool):
        self._has_access = has_access
        self.calls: list[uuid.UUID] = []

    async def has_third_party_access(self, user_id: uuid.UUID) -> bool:
        self.calls.append(user_id)
        return self._has_access


class _FakeUserDirectory:
    def __init__(self, org_id: uuid.UUID | None):
        self._org_id = org_id
        self.calls: list[uuid.UUID] = []

    async def get_org_id(self, user_id: uuid.UUID) -> uuid.UUID | None:
        self.calls.append(user_id)
        return self._org_id


def _access(
    has_third_party_access: bool = False, elder_org_id: uuid.UUID | None = None
) -> tuple[ElderAccessContext, _FakeConsentDirectory, _FakeUserDirectory]:
    consent = _FakeConsentDirectory(has_third_party_access)
    users = _FakeUserDirectory(elder_org_id)
    return ElderAccessContext(consent=consent, users=users), consent, users  # type: ignore[arg-type]


async def test_family_allowed_without_consent_or_org_check() -> None:
    """가족(위탁범위 내 이용)은 third_party_access 동의·org 여부와 무관하게 통과 —
    두 조회 모두 일어나지 않아야 한다(불필요한 DB 왕복 방지)."""
    elder = uuid.uuid4()
    ctx = _ctx(_member(elder, FamilyRole.FAMILY))
    access, consent, users = _access(has_third_party_access=False)

    await authorize_elder_data_read(ctx, elder, access)

    assert consent.calls == []
    assert users.calls == []


async def test_caregiver_without_org_allowed_without_checks() -> None:
    """org_id 없는(B2C) caregiver는 동의·테넌시 체크 둘 다 안 탄다."""
    elder = uuid.uuid4()
    ctx = _ctx(_member(elder, FamilyRole.CAREGIVER))
    access, consent, users = _access()

    await authorize_elder_data_read(ctx, elder, access)

    assert consent.calls == []
    assert users.calls == []


async def test_social_worker_denied_without_consent() -> None:
    elder = uuid.uuid4()
    ctx = _ctx(_member(elder, FamilyRole.SOCIAL_WORKER))
    access, consent, _ = _access(has_third_party_access=False)

    with pytest.raises(ApiError, match="제3자 제공 동의"):
        await authorize_elder_data_read(ctx, elder, access)

    assert consent.calls == [elder]


async def test_social_worker_allowed_with_consent_and_no_org() -> None:
    elder = uuid.uuid4()
    ctx = _ctx(_member(elder, FamilyRole.SOCIAL_WORKER))
    access, consent, users = _access(has_third_party_access=True)

    await authorize_elder_data_read(ctx, elder, access)

    assert consent.calls == [elder]
    assert users.calls == []  # org_id 없는 구성원은 테넌시 체크 자체를 안 함


async def test_admin_bypasses_all_checks() -> None:
    elder = uuid.uuid4()
    ctx = _ctx(_member(uuid.uuid4(), FamilyRole.ADMIN))
    access, consent, users = _access(has_third_party_access=False)

    await authorize_elder_data_read(ctx, elder, access)

    assert consent.calls == []
    assert users.calls == []


async def test_device_identity_bypasses_all_checks() -> None:
    """기기(어르신 본인)는 항상 자기 자신 데이터라 두 분기 자체를 안 탄다."""
    elder = uuid.uuid4()
    device = DeviceIdentity(device_id=uuid.uuid4(), user_id=elder)
    access, consent, users = _access(has_third_party_access=False)

    await authorize_elder_data_read(device, elder, access)

    assert consent.calls == []
    assert users.calls == []


async def test_social_worker_without_membership_still_forbidden_by_base_check() -> None:
    """연결 안 된 어르신은 authorize_user_access 단계에서 이미 막힌다 —
    동의·테넌시 조회까지 가지 않는다."""
    elder = uuid.uuid4()
    ctx = _ctx(_member(uuid.uuid4(), FamilyRole.SOCIAL_WORKER))
    access, consent, users = _access(has_third_party_access=True)

    with pytest.raises(ApiError, match="연결"):
        await authorize_elder_data_read(ctx, elder, access)

    assert consent.calls == []
    assert users.calls == []


# --- B2G 시설 테넌시 안전망 (decisions.md #59, I2) ------------------------------


async def test_org_affiliated_caregiver_same_org_allowed() -> None:
    elder = uuid.uuid4()
    org = uuid.uuid4()
    ctx = _ctx(_member(elder, FamilyRole.CAREGIVER, org_id=org))
    access, _, users = _access(elder_org_id=org)

    await authorize_elder_data_read(ctx, elder, access)

    assert users.calls == [elder]


async def test_org_affiliated_caregiver_different_org_denied() -> None:
    """설정 실수로 다른 시설 caregiver가 이 어르신에 연결돼 있어도 org가 다르면 차단."""
    elder = uuid.uuid4()
    staff_org, elder_org = uuid.uuid4(), uuid.uuid4()
    ctx = _ctx(_member(elder, FamilyRole.CAREGIVER, org_id=staff_org))
    access, _, users = _access(elder_org_id=elder_org)

    with pytest.raises(ApiError, match="다른 시설"):
        await authorize_elder_data_read(ctx, elder, access)

    assert users.calls == [elder]


async def test_org_affiliated_caregiver_elder_without_org_denied() -> None:
    """직원은 시설 소속인데 어르신은 어느 시설에도 없으면(개인) 역시 불일치로 차단."""
    elder = uuid.uuid4()
    ctx = _ctx(_member(elder, FamilyRole.CAREGIVER, org_id=uuid.uuid4()))
    access, _, _ = _access(elder_org_id=None)

    with pytest.raises(ApiError, match="다른 시설"):
        await authorize_elder_data_read(ctx, elder, access)


async def test_org_affiliated_social_worker_needs_both_consent_and_org_match() -> None:
    """social_worker는 두 체크(동의+테넌시) 다 통과해야 한다 — 동의만 있고
    시설이 다르면 여전히 차단."""
    elder = uuid.uuid4()
    staff_org, elder_org = uuid.uuid4(), uuid.uuid4()
    ctx = _ctx(_member(elder, FamilyRole.SOCIAL_WORKER, org_id=staff_org))
    access, consent, users = _access(has_third_party_access=True, elder_org_id=elder_org)

    with pytest.raises(ApiError, match="다른 시설"):
        await authorize_elder_data_read(ctx, elder, access)

    assert consent.calls == [elder]  # 동의 체크는 먼저 통과했다
    assert users.calls == [elder]
