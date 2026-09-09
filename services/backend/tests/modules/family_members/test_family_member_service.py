"""FamilyMemberService 유닛 테스트 — 페이크 Repository로 DB 없이 Application 계층 검증."""

import uuid
from datetime import UTC, datetime

import pytest

from core_service.core.errors import ApiError
from core_service.modules.family_members.application.family_member_service import (
    FamilyMemberService,
)
from core_service.modules.family_members.domain.family_member import FamilyMember, FamilyRole


class FakeFamilyMemberRepository:
    def __init__(self) -> None:
        self._store: dict[uuid.UUID, FamilyMember] = {}

    async def get_by_id(self, family_member_id: uuid.UUID) -> FamilyMember | None:
        return self._store.get(family_member_id)

    async def list_by_user(self, user_id: uuid.UUID) -> list[FamilyMember]:
        return [m for m in self._store.values() if m.user_id == user_id]

    async def create(
        self,
        user_id: uuid.UUID,
        role: FamilyRole,
        name: str,
        contact: str,
        keycloak_sub: str | None = None,
    ) -> FamilyMember:
        member = FamilyMember(
            id=uuid.uuid4(),
            user_id=user_id,
            role=role,
            name=name,
            contact=contact,
            two_factor_enabled=False,
            keycloak_sub=keycloak_sub,
            created_at=datetime.now(UTC),
        )
        self._store[member.id] = member
        return member


@pytest.fixture
def service() -> FamilyMemberService:
    return FamilyMemberService(FakeFamilyMemberRepository())  # type: ignore[arg-type]


async def test_create_family_member_succeeds(service: FamilyMemberService) -> None:
    member = await service.create_family_member(
        user_id=uuid.uuid4(), role=FamilyRole.FAMILY, name="김민지", contact="010-1234-5678"
    )
    assert member.role == FamilyRole.FAMILY
    assert member.two_factor_enabled is False
    assert member.keycloak_sub is None  # 임시 직접생성 경로는 계정 미연결


async def test_create_family_member_binds_keycloak_sub_from_invitation_accept(
    service: FamilyMemberService,
) -> None:
    """초대 수락 흐름: 수락자의 토큰 sub를 새 구성원에 박아넣어야 이후 로그인이 된다."""
    member = await service.create_family_member(
        user_id=uuid.uuid4(),
        role=FamilyRole.CAREGIVER,
        name="박복지",
        contact="010-9999-0000",
        keycloak_sub="kc-sub-abc",
    )
    assert member.keycloak_sub == "kc-sub-abc"


async def test_create_family_member_rejects_empty_name(service: FamilyMemberService) -> None:
    with pytest.raises(ApiError) as exc_info:
        await service.create_family_member(
            user_id=uuid.uuid4(), role=FamilyRole.CAREGIVER, name="", contact="010-0000-0000"
        )
    assert exc_info.value.code == "VALIDATION_ERROR"


async def test_create_family_member_rejects_empty_contact(service: FamilyMemberService) -> None:
    with pytest.raises(ApiError) as exc_info:
        await service.create_family_member(
            user_id=uuid.uuid4(), role=FamilyRole.SOCIAL_WORKER, name="박복지", contact=""
        )
    assert exc_info.value.code == "VALIDATION_ERROR"


async def test_get_family_member_not_found_raises(service: FamilyMemberService) -> None:
    with pytest.raises(ApiError) as exc_info:
        await service.get_family_member(uuid.uuid4())
    assert exc_info.value.code == "NOT_FOUND"


async def test_list_family_members_for_user_filters_correctly(service: FamilyMemberService) -> None:
    user_id = uuid.uuid4()
    other_user_id = uuid.uuid4()
    await service.create_family_member(
        user_id=user_id, role=FamilyRole.FAMILY, name="A", contact="010-1111-1111"
    )
    await service.create_family_member(
        user_id=other_user_id, role=FamilyRole.FAMILY, name="B", contact="010-2222-2222"
    )
    members = await service.list_family_members_for_user(user_id)
    assert len(members) == 1
    assert members[0].name == "A"
