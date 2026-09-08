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
