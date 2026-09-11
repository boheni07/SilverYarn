"""UserService 유닛 테스트 — 실 DB 없이 Repository를 페이크로 대체(Domain/Application 계층 테스트)."""

import uuid
from datetime import UTC, datetime

import pytest

from core_service.core.errors import ApiError
from core_service.modules.users.application.user_service import UserService
from core_service.modules.users.domain.user import PersonaSnapshot, User


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

    async def list_all(self, offset: int, limit: int, name: str | None = None) -> tuple[list[User], int]:
        users = list(self._store.values())
        if name:
            users = [u for u in users if name.lower() in u.name.lower()]
        users.sort(key=lambda u: u.created_at, reverse=True)
        return users[offset : offset + limit], len(users)

    async def set_persona_snapshot(self, user_id, *, summary, keywords, source_chapter_count):
        user = self._store[user_id]
        user.persona_snapshot = PersonaSnapshot(
            summary=summary, keywords=list(keywords), source_chapter_count=source_chapter_count
        )


class FakeSummarizer:
    """§2.11 4단계 — LLMClient.summarize_persona_memory 대역."""

    def __init__(self, fail: bool = False, summary: str = "요약된 인생 이야기"):
        self._fail = fail
        self._summary = summary

    async def summarize_persona_memory(self, chapter_digests: list[tuple[str, list[str]]]):
        if self._fail:
            raise RuntimeError("페르소나 요약 실패")
        return self._summary, ["키워드1", "키워드2"]


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


class TestListUsersNameSearch:
    """이름 부분일치 검색(2026-09-08 신규)."""

    async def test_이름_부분일치로_좁혀진다(self, service: UserService) -> None:
        await service.create_user(name="김순자", birth_date=None)
        await service.create_user(name="박영희", birth_date=None)
        await service.create_user(name="김철수", birth_date=None)

        users, total = await service.list_users(page=1, page_size=20, name="김")

        assert total == 2
        assert {u.name for u in users} == {"김순자", "김철수"}

    async def test_대소문자_구분_없음(self, service: UserService) -> None:
        await service.create_user(name="TestUser", birth_date=None)

        users, total = await service.list_users(page=1, page_size=20, name="testuser")

        assert total == 1

    async def test_일치하는_사용자_없으면_빈_목록(self, service: UserService) -> None:
        await service.create_user(name="김순자", birth_date=None)

        users, total = await service.list_users(page=1, page_size=20, name="존재하지않음")

        assert users == []
        assert total == 0

    async def test_name_생략하면_전체_반환(self, service: UserService) -> None:
        await service.create_user(name="김순자", birth_date=None)
        await service.create_user(name="박영희", birth_date=None)

        users, total = await service.list_users(page=1, page_size=20)

        assert total == 2


class TestPersonaSnapshot:
    """§2.11 4단계 "단기 압축 기억" — 여러 챕터를 가로지른 요약(2026-09-11 신규)."""

    async def test_챕터_요약이_없으면_생성하지_않는다(self, service: UserService) -> None:
        user = await service.create_user(name="김순자", birth_date=None)

        result = await service.refresh_persona_snapshot(user.id, [], FakeSummarizer())

        assert result.persona_snapshot is None

    async def test_챕터_요약이_있으면_생성한다(self, service: UserService) -> None:
        user = await service.create_user(name="김순자", birth_date=None)
        digests = [("1978년 인천 공장 이야기", ["인천", "공장"])]

        result = await service.refresh_persona_snapshot(user.id, digests, FakeSummarizer())

        assert result.persona_snapshot is not None
        assert result.persona_snapshot.summary == "요약된 인생 이야기"
        assert result.persona_snapshot.keywords == ["키워드1", "키워드2"]
        assert result.persona_snapshot.source_chapter_count == 1

    async def test_참고_챕터_수가_그대로면_재호출하지_않는다(self, service: UserService) -> None:
        user = await service.create_user(name="김순자", birth_date=None)
        digests = [("요약1", ["k1"])]
        await service.refresh_persona_snapshot(user.id, digests, FakeSummarizer(summary="첫 요약"))

        result = await service.refresh_persona_snapshot(
            user.id, digests, FakeSummarizer(summary="다시 부르면 안 되는 요약")
        )

        assert result.persona_snapshot.summary == "첫 요약"  # 재호출 안 됐으므로 그대로

    async def test_참고_챕터_수가_바뀌면_재생성한다(self, service: UserService) -> None:
        user = await service.create_user(name="김순자", birth_date=None)
        first = FakeSummarizer(summary="첫 요약")
        await service.refresh_persona_snapshot(user.id, [("요약1", ["k1"])], first)

        result = await service.refresh_persona_snapshot(
            user.id, [("요약1", ["k1"]), ("요약2", ["k2"])], FakeSummarizer(summary="갱신된 요약")
        )

        assert result.persona_snapshot.summary == "갱신된 요약"
        assert result.persona_snapshot.source_chapter_count == 2

    async def test_force면_챕터_수가_같아도_재생성한다(self, service: UserService) -> None:
        user = await service.create_user(name="김순자", birth_date=None)
        digests = [("요약1", ["k1"])]
        await service.refresh_persona_snapshot(user.id, digests, FakeSummarizer(summary="첫 요약"))

        result = await service.refresh_persona_snapshot(
            user.id, digests, FakeSummarizer(summary="강제 갱신된 요약"), force=True
        )

        assert result.persona_snapshot.summary == "강제 갱신된 요약"

    async def test_요약_실패시_예외가_전파된다(self, service: UserService) -> None:
        """실패 시 이전 스냅샷 유지는 호출자(업로드 파이프라인)의 책임 — 서비스 자체는
        예외를 삼키지 않는다(ChapterService.compact_chapter와 동일한 원칙)."""
        user = await service.create_user(name="김순자", birth_date=None)

        with pytest.raises(RuntimeError):
            await service.refresh_persona_snapshot(user.id, [("요약1", ["k1"])], FakeSummarizer(fail=True))
