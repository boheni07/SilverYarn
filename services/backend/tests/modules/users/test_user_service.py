"""UserService 유닛 테스트 — 실 DB 없이 Repository를 페이크로 대체(Domain/Application 계층 테스트)."""

import uuid
from datetime import UTC, datetime

import pytest

from core_service.core.errors import ApiError
from core_service.modules.users.application.user_service import UserService
from core_service.modules.users.domain.user import User


class FakeUserRepository:
    def __init__(self) -> None:
        self._store: dict[uuid.UUID, User] = {}

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return self._store.get(user_id)

    async def create(self, name: str, birth_date=None) -> User:
        user = User(
            id=uuid.uuid4(),
            name=name,
            birth_date=birth_date,
            primary_device_id=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        self._store[user.id] = user
        return user

    async def list_all(self, offset: int, limit: int) -> tuple[list[User], int]:
        users = sorted(self._store.values(), key=lambda u: u.created_at, reverse=True)
        return users[offset : offset + limit], len(users)


@pytest.fixture
def service() -> UserService:
    return UserService(FakeUserRepository())  # type: ignore[arg-type]


async def test_create_user_succeeds(service: UserService) -> None:
    user = await service.create_user(name="김순자", birth_date=None)
    assert user.name == "김순자"
    assert user.id is not None


async def test_create_user_rejects_empty_name(service: UserService) -> None:
    with pytest.raises(ApiError) as exc_info:
        await service.create_user(name="", birth_date=None)
    assert exc_info.value.code == "VALIDATION_ERROR"


async def test_get_user_not_found_raises_api_error(service: UserService) -> None:
    with pytest.raises(ApiError) as exc_info:
        await service.get_user(uuid.uuid4())
    assert exc_info.value.code == "NOT_FOUND"


async def test_get_user_returns_created_user(service: UserService) -> None:
    created = await service.create_user(name="박영희", birth_date=None)
    fetched = await service.get_user(created.id)
    assert fetched.id == created.id
    assert fetched.name == "박영희"


class TestListUsers:
    """apps/admin "전체 사용자 목록" 화면용(2026-09-08 신규)."""

    async def test_전체_개수와_페이지_크기만큼만_반환(self, service: UserService) -> None:
        for i in range(5):
            await service.create_user(name=f"사용자{i}", birth_date=None)

        users, total = await service.list_users(page=1, page_size=2)

        assert total == 5
        assert len(users) == 2

    async def test_두번째_페이지는_다음_항목들(self, service: UserService) -> None:
        for i in range(5):
            await service.create_user(name=f"사용자{i}", birth_date=None)

        page1, _ = await service.list_users(page=1, page_size=2)
        page2, _ = await service.list_users(page=2, page_size=2)

        assert {u.id for u in page1}.isdisjoint({u.id for u in page2})

    async def test_page가_0_이하면_VALIDATION_ERROR(self, service: UserService) -> None:
        with pytest.raises(ApiError) as exc_info:
            await service.list_users(page=0, page_size=20)
        assert exc_info.value.code == "VALIDATION_ERROR"

    async def test_page_size가_범위_밖이면_VALIDATION_ERROR(self, service: UserService) -> None:
        with pytest.raises(ApiError) as exc_info:
            await service.list_users(page=1, page_size=101)
        assert exc_info.value.code == "VALIDATION_ERROR"

    async def test_사용자_없으면_빈_목록과_total_0(self, service: UserService) -> None:
        users, total = await service.list_users(page=1, page_size=20)
        assert users == []
        assert total == 0
