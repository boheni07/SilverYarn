"""SyncService 유닛 테스트 — 페이크 Repository로 DB 없이 Application 계층 검증.

핵심 검증 대상: apps/admin 동기화 모니터링 화면이 쓰는 list_sessions()가
- device_id를 주면 기기 하나로 정확히 필터링하고
- device_id를 생략하면(전체 기기 통합 모니터링, 신규) 모든 기기를 아우르고
- status를 주면 그 상태만 골라내고
- 항상 started_at 내림차순(최신 우선)을 지키는지 — Repository의 idx_sync_device /
  idx_sync_started_at(schema.md v1.5) 인덱스 활용을 전제로 한 정렬 계약이다.
"""

import uuid
from datetime import UTC, datetime, timedelta

import pytest

from core_service.core.errors import ApiError
from core_service.modules.sync.application.sync_service import SyncService
from core_service.modules.sync.domain.sync_session import SyncDirection, SyncSession, SyncStatus


class FakeSyncSessionRepository:
    def __init__(self) -> None:
        self.by_id: dict[uuid.UUID, SyncSession] = {}

    async def get_by_id(self, session_id: uuid.UUID) -> SyncSession | None:
        return self.by_id.get(session_id)

    async def create(self, device_id: uuid.UUID, direction: SyncDirection, checksum: str) -> SyncSession:
        session = SyncSession(
            id=uuid.uuid4(),
            device_id=device_id,
            direction=direction,
            status=SyncStatus.RETRYING,
            checksum=checksum,
            retry_count=0,
            started_at=datetime.now(UTC),
            finished_at=None,
        )
        self.by_id[session.id] = session
        return session

    async def update_status(
        self, session_id: uuid.UUID, status: SyncStatus, increment_retry: bool = False
    ) -> SyncSession:
        session = self.by_id[session_id]
        session.status = status
        if increment_retry:
            session.retry_count += 1
        if status in (SyncStatus.SUCCESS, SyncStatus.FAILED):
            session.finished_at = datetime.now(UTC)
        return session

    async def list_all(
        self,
        offset: int,
        limit: int,
        device_id: uuid.UUID | None = None,
        status: SyncStatus | None = None,
    ) -> tuple[list[SyncSession], int]:
        sessions = list(self.by_id.values())
        if device_id is not None:
            sessions = [s for s in sessions if s.device_id == device_id]
        if status is not None:
            sessions = [s for s in sessions if s.status == status]
        sessions.sort(key=lambda s: s.started_at, reverse=True)
        total = len(sessions)
        return sessions[offset : offset + limit], total


@pytest.fixture
def repo() -> FakeSyncSessionRepository:
    return FakeSyncSessionRepository()


@pytest.fixture
def service(repo: FakeSyncSessionRepository) -> SyncService:
    return SyncService(repo, arq_pool=None)  # type: ignore[arg-type]  # 아래 테스트는 잡 큐를 안 씀


async def _add_session(
    repo: FakeSyncSessionRepository, device_id: uuid.UUID, started_at: datetime, status: SyncStatus
) -> SyncSession:
    session = SyncSession(
        id=uuid.uuid4(),
        device_id=device_id,
        direction=SyncDirection.UPLOAD,
        status=status,
        checksum="abc123",
        retry_count=0,
        started_at=started_at,
        finished_at=None,
    )
    repo.by_id[session.id] = session
    return session


class TestListSessionsByDevice:
    """device_id 지정 — 기존 devices → sync-monitor 화면(기기 하나)."""

    async def test_필터링_다른_기기_세션은_제외(
        self, service: SyncService, repo: FakeSyncSessionRepository
    ) -> None:
        device_a = uuid.uuid4()
        device_b = uuid.uuid4()
        now = datetime.now(UTC)
        await _add_session(repo, device_a, now, SyncStatus.SUCCESS)
        await _add_session(repo, device_b, now, SyncStatus.SUCCESS)

        result, total = await service.list_sessions(page=1, page_size=20, device_id=device_a)

        assert total == 1
        assert len(result) == 1
        assert result[0].device_id == device_a

    async def test_최신_세션이_먼저_온다(self, service: SyncService, repo: FakeSyncSessionRepository) -> None:
        device_id = uuid.uuid4()
        now = datetime.now(UTC)
        older = await _add_session(repo, device_id, now - timedelta(hours=1), SyncStatus.SUCCESS)
        newer = await _add_session(repo, device_id, now, SyncStatus.FAILED)

        result, _ = await service.list_sessions(page=1, page_size=20, device_id=device_id)

        assert [s.id for s in result] == [newer.id, older.id]

    async def test_세션_없는_기기는_빈_목록(self, service: SyncService) -> None:
        result, total = await service.list_sessions(page=1, page_size=20, device_id=uuid.uuid4())
        assert result == []
        assert total == 0


class TestListAllSessions:
    """device_id 생략 — "전체 기기 통합 모니터링"(신규)."""

    async def test_모든_기기의_세션을_아우른다(
        self, service: SyncService, repo: FakeSyncSessionRepository
    ) -> None:
        now = datetime.now(UTC)
        await _add_session(repo, uuid.uuid4(), now, SyncStatus.SUCCESS)
        await _add_session(repo, uuid.uuid4(), now, SyncStatus.FAILED)
        await _add_session(repo, uuid.uuid4(), now, SyncStatus.RETRYING)

        result, total = await service.list_sessions(page=1, page_size=20)

        assert total == 3
        assert len(result) == 3

    async def test_status_필터(self, service: SyncService, repo: FakeSyncSessionRepository) -> None:
        now = datetime.now(UTC)
        await _add_session(repo, uuid.uuid4(), now, SyncStatus.SUCCESS)
        failed = await _add_session(repo, uuid.uuid4(), now, SyncStatus.FAILED)
        await _add_session(repo, uuid.uuid4(), now, SyncStatus.RETRYING)

        result, total = await service.list_sessions(page=1, page_size=20, status=SyncStatus.FAILED)

        assert total == 1
        assert result == [failed]

    async def test_페이지네이션_경계(self, service: SyncService, repo: FakeSyncSessionRepository) -> None:
        now = datetime.now(UTC)
        for i in range(5):
            await _add_session(repo, uuid.uuid4(), now - timedelta(minutes=i), SyncStatus.SUCCESS)

        page1, total = await service.list_sessions(page=1, page_size=2)
        page2, _ = await service.list_sessions(page=2, page_size=2)

        assert total == 5
        assert len(page1) == 2
        assert {s.id for s in page1}.isdisjoint({s.id for s in page2})

    async def test_page가_0_이하면_VALIDATION_ERROR(self, service: SyncService) -> None:
        with pytest.raises(ApiError) as exc_info:
            await service.list_sessions(page=0, page_size=20)
        assert exc_info.value.code == "VALIDATION_ERROR"

    async def test_page_size가_범위_밖이면_VALIDATION_ERROR(self, service: SyncService) -> None:
        with pytest.raises(ApiError) as exc_info:
            await service.list_sessions(page=1, page_size=101)
        assert exc_info.value.code == "VALIDATION_ERROR"


class TestGetSessionStatus:
    async def test_존재하지_않는_세션은_NOT_FOUND(self, service: SyncService) -> None:
        with pytest.raises(ApiError) as exc_info:
            await service.get_session_status(uuid.uuid4())
        assert exc_info.value.code == "NOT_FOUND"

    async def test_존재하는_세션_조회(self, service: SyncService, repo: FakeSyncSessionRepository) -> None:
        device_id = uuid.uuid4()
        session = await _add_session(repo, device_id, datetime.now(UTC), SyncStatus.RETRYING)

        result = await service.get_session_status(session.id)

        assert result.id == session.id
