"""User 유스케이스 — Presentation은 이 서비스만 호출하고 Repository를 직접 만지지 않는다."""

import uuid
from datetime import date

from core_service.core.errors import ApiError
from core_service.modules.users.domain.user import User
from core_service.modules.users.infrastructure.user_repository import UserRepository


class UserService:
    def __init__(self, repo: UserRepository):
        self._repo = repo

    async def get_user(self, user_id: uuid.UUID) -> User:
        user = await self._repo.get_by_id(user_id)
        if user is None:
            raise ApiError("NOT_FOUND", f"사용자({user_id})를 찾을 수 없습니다.")
        return user

    async def create_user(self, name: str, birth_date: date | None) -> User:
        if not name or len(name) > 100:
            raise ApiError("VALIDATION_ERROR", "name은 1~100자여야 합니다.")
        return await self._repo.create(name=name, birth_date=birth_date)

    async def list_users(self, page: int, page_size: int) -> tuple[list[User], int]:
        """apps/admin "전체 사용자 목록" — page는 1부터 시작(design.md §4.1 예시와 동일)."""
        if page < 1:
            raise ApiError("VALIDATION_ERROR", "page는 1 이상이어야 합니다.")
        if not (1 <= page_size <= 100):
            raise ApiError("VALIDATION_ERROR", "page_size는 1~100 사이여야 합니다.")
        offset = (page - 1) * page_size
        return await self._repo.list_all(offset=offset, limit=page_size)
