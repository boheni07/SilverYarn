"""InvitationService 유닛 테스트 — 페이크 Repository로 DB 없이 Application 계층 검증."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest

from core_service.core.errors import ApiError
from core_service.modules.invitations.application.invitation_service import InvitationService
from core_service.modules.invitations.domain.invitation import Invitation, InvitationStatus
from core_service.shared.domain_enums import FamilyRole


class FakeInvitationRepository:
    def __init__(self) -> None:
        self._store: dict[uuid.UUID, Invitation] = {}

    async def get_by_id(self, invitation_id: uuid.UUID) -> Invitation | None:
        return self._store.get(invitation_id)

    async def get_by_token(self, token: str) -> Invitation | None:
        return next((i for i in self._store.values() if i.token == token), None)

    async def list_by_user(self, user_id: uuid.UUID) -> list[Invitation]:
        return [i for i in self._store.values() if i.user_id == user_id]

    async def exists_pending_for_contact(self, user_id: uuid.UUID, contact: str) -> bool:
        return any(
            i.user_id == user_id and i.contact == contact and i.status == InvitationStatus.PENDING
            for i in self._store.values()
        )

    async def create(
        self,
        user_id: uuid.UUID,
        invited_by: uuid.UUID | None,
        contact: str,
        role: FamilyRole,
        token: str,
        expires_at: datetime,
    ) -> Invitation:
        invitation = Invitation(
            id=uuid.uuid4(),
            user_id=user_id,
            invited_by=invited_by,
            contact=contact,
            role=role,
            token=token,
            status=InvitationStatus.PENDING,
            created_at=datetime.now(UTC),
            expires_at=expires_at,
        )
        self._store[invitation.id] = invitation
        return invitation

    async def update_status(self, invitation_id: uuid.UUID, status: InvitationStatus) -> Invitation:
        invitation = self._store[invitation_id]
        invitation.status = status
        return invitation


@pytest.fixture
def repo() -> FakeInvitationRepository:
    return FakeInvitationRepository()


@pytest.fixture
def service(repo: FakeInvitationRepository) -> InvitationService:
    return InvitationService(repo)  # type: ignore[arg-type]


async def test_create_invitation_generates_pending_with_token(service: InvitationService) -> None:
    invitation = await service.create_invitation(
        user_id=uuid.uuid4(), invited_by=None, contact="010-1234-5678", role=FamilyRole.FAMILY
    )
    assert invitation.status == InvitationStatus.PENDING
    assert len(invitation.token) > 20
    assert invitation.expires_at > datetime.now(UTC)


async def test_create_invitation_rejects_duplicate_pending_contact(service: InvitationService) -> None:
    user_id = uuid.uuid4()
    await service.create_invitation(
        user_id=user_id, invited_by=None, contact="010-1234-5678", role=FamilyRole.FAMILY
    )
    with pytest.raises(ApiError) as exc:
        await service.create_invitation(
            user_id=user_id, invited_by=None, contact="010-1234-5678", role=FamilyRole.CAREGIVER
        )
    assert exc.value.code == "CONFLICT"


async def test_create_invitation_rejects_empty_contact(service: InvitationService) -> None:
    with pytest.raises(ApiError) as exc_info:
        await service.create_invitation(
            user_id=uuid.uuid4(), invited_by=None, contact="", role=FamilyRole.FAMILY
        )
    assert exc_info.value.code == "VALIDATION_ERROR"


async def test_get_invitation_by_token_not_found(service: InvitationService) -> None:
    with pytest.raises(ApiError) as exc_info:
        await service.get_invitation_by_token("no-such-token")
    assert exc_info.value.code == "NOT_FOUND"


async def test_validate_and_consume_accepts_pending_invitation(service: InvitationService) -> None:
    invitation = await service.create_invitation(
        user_id=uuid.uuid4(), invited_by=None, contact="010-1234-5678", role=FamilyRole.CAREGIVER
    )
    result = await service.validate_and_consume(invitation.token)
    assert result.status == InvitationStatus.ACCEPTED


async def test_validate_and_consume_rejects_already_accepted(service: InvitationService) -> None:
    invitation = await service.create_invitation(
        user_id=uuid.uuid4(), invited_by=None, contact="010-1234-5678", role=FamilyRole.FAMILY
    )
    await service.validate_and_consume(invitation.token)
    with pytest.raises(ApiError) as exc_info:
        await service.validate_and_consume(invitation.token)
    assert exc_info.value.code == "CONFLICT"


async def test_validate_and_consume_marks_expired_lazily(
    service: InvitationService, repo: FakeInvitationRepository
) -> None:
    invitation = await service.create_invitation(
        user_id=uuid.uuid4(), invited_by=None, contact="010-1234-5678", role=FamilyRole.FAMILY
    )
    # 이미 만료된 것처럼 시간 조작 (실제로는 DEFAULT_EXPIRY_DAYS 경과)
    stored = await repo.get_by_id(invitation.id)
    stored.expires_at = datetime.now(UTC) - timedelta(seconds=1)

    with pytest.raises(ApiError) as exc_info:
        await service.validate_and_consume(invitation.token)
    assert exc_info.value.code == "CONFLICT"

    refreshed = await repo.get_by_token(invitation.token)
    assert refreshed.status == InvitationStatus.EXPIRED
