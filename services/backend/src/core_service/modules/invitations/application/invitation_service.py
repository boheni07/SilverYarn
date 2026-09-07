"""Invitation 유스케이스.

family_member 생성 자체는 이 서비스가 하지 않는다 — `accept_invitation()`은 초대
검증과 pending→accepted 상태 전이만 책임지고, 실제 family_members 행 생성은
api 레이어가 family_members/deps.py를 통해 별도로 수행한다(구성은 composition
root인 api 레이어 책임, structure.md §2 "모듈 간 재사용" 참조). 두 작업이 같은
요청의 같은 DB 세션(FastAPI Depends 캐싱)에서 실행되므로 트랜잭션은 하나로 묶인다.
"""

import secrets
import uuid
from datetime import datetime, timedelta

from core_service.core.errors import ApiError
from core_service.modules.invitations.domain.invitation import (
    DEFAULT_EXPIRY_DAYS,
    Invitation,
    InvitationStatus,
)
from core_service.modules.invitations.infrastructure.invitation_repository import (
    InvitationRepository,
)
from core_service.shared.domain_enums import FamilyRole


class InvitationService:
    def __init__(self, repo: InvitationRepository):
        self._repo = repo

    async def create_invitation(
        self,
        user_id: uuid.UUID,
        invited_by: uuid.UUID | None,
        contact: str,
        role: FamilyRole,
    ) -> Invitation:
        if not contact or len(contact) > 100:
            raise ApiError("VALIDATION_ERROR", "contact는 1~100자여야 합니다.")
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(days=DEFAULT_EXPIRY_DAYS)
        return await self._repo.create(
            user_id=user_id,
            invited_by=invited_by,
            contact=contact,
            role=role,
            token=token,
            expires_at=expires_at,
        )

    async def get_invitation_by_token(self, token: str) -> Invitation:
        invitation = await self._repo.get_by_token(token)
        if invitation is None:
            raise ApiError("NOT_FOUND", "초대를 찾을 수 없습니다.")
        return invitation

    async def list_invitations_for_user(self, user_id: uuid.UUID) -> list[Invitation]:
        return await self._repo.list_by_user(user_id)

    async def validate_and_consume(self, token: str) -> Invitation:
        """수락 가능 여부를 검증하고 status=accepted로 전이한다.

        만료된 초대를 우연히 발견하면(지연 만료 처리) status=expired로 갱신하고
        CONFLICT를 던진다 — 별도 배치잡 없이도 다음 조회 시 정확한 상태를 보장한다.
        """
        invitation = await self.get_invitation_by_token(token)
        try:
            invitation.ensure_acceptable()
        except ValueError as exc:
            if invitation.is_expired() and invitation.status == InvitationStatus.PENDING:
                await self._repo.update_status(invitation.id, InvitationStatus.EXPIRED)
            raise ApiError("CONFLICT", str(exc)) from exc

        return await self._repo.update_status(invitation.id, InvitationStatus.ACCEPTED)
