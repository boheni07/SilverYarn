"""FamilyMember 유스케이스."""

import uuid

from core_service.core.errors import ApiError
from core_service.modules.family_members.domain.family_member import FamilyMember, FamilyRole
from core_service.modules.family_members.infrastructure.family_member_repository import (
    FamilyMemberRepository,
)


class FamilyMemberService:
    def __init__(self, repo: FamilyMemberRepository):
        self._repo = repo

    async def get_family_member(self, family_member_id: uuid.UUID) -> FamilyMember:
        member = await self._repo.get_by_id(family_member_id)
        if member is None:
            raise ApiError("NOT_FOUND", f"가족/복지사 구성원({family_member_id})을 찾을 수 없습니다.")
        return member

    async def list_family_members_for_user(self, user_id: uuid.UUID) -> list[FamilyMember]:
        return await self._repo.list_by_user(user_id)

    async def create_family_member(
        self,
        user_id: uuid.UUID,
        role: FamilyRole,
        name: str,
        contact: str,
        keycloak_sub: str | None = None,
    ) -> FamilyMember:
        """초대 수락(invitations) 또는 임시 직접생성 경로.

        `keycloak_sub`: 수락 흐름에서 넘어온다 — 이 값이 있어야 이후 `require_family`가
        그 사람의 토큰 `sub`로 이 행을 찾아 로그인시킬 수 있다(없으면 계정 연결이 안 됨).
        """
        if not name or len(name) > 100:
            raise ApiError("VALIDATION_ERROR", "name은 1~100자여야 합니다.")
        if not contact or len(contact) > 100:
            raise ApiError("VALIDATION_ERROR", "contact는 1~100자여야 합니다.")
        return await self._repo.create(
            user_id=user_id, role=role, name=name, contact=contact, keycloak_sub=keycloak_sub
        )
