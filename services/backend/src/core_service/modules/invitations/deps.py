"""invitations 모듈의 공개 조합 지점 — family_members/deps.py와 동일한 패턴."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core_service.core.db import get_db
from core_service.modules.invitations.application.invitation_service import InvitationService
from core_service.modules.invitations.infrastructure.invitation_repository import (
    InvitationRepository,
)


def get_invitation_service(session: AsyncSession = Depends(get_db)) -> InvitationService:
    return InvitationService(InvitationRepository(session))
