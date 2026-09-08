"""SyncService 유닛 테스트 — 페이크 Repository로 DB 없이 Application 계층 검증.

핵심 검증 대상: apps/admin 동기화 모니터링 화면이 쓰는 list_sessions_for_device()가
device_id로 정확히 필터링하고 started_at 내림차순(최신 우선)을 지키는지 — Repository의
idx_sync_device(device_id, started_at DESC) 인덱스 활용을 전제로 한 정렬 계약이다.
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

    async def list_by_device(self, device_id: uuid.UUID, limit: int = 50) -> list[SyncSession]:
        sessions = [s for s in self.by_id.values() if s.device_id == device_id]
        return sorted(sessions, key=lambda s: s.started_at, reverse=True)[:limit]


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


class TestListSessionsForDevice:
    async def test_필터링_다른_기기_세션은_제외(
        self, service: SyncService, repo: FakeSyncSessionRepository
    ) -> None:
        device_a = uuid.uuid4()
        device_b = uuid.uuid4()
        now = datetime.now(UTC)
        await _add_session(repo, device_a, now, SyncStatus.SUCCESS)
        await _add_session(repo, device_b, now, SyncStatus.SUCCESS)

        result = await service.list_sessions_for_device(device_a)

        assert len(result) == 1
        assert result[0].device_id == device_a

    async def test_최신_세션이_먼저_온다(self, service: SyncService, repo: FakeSyncSessionRepository) -> None:
        device_id = uuid.uuid4()
        now = datetime.now(UTC)
        older = await _add_session(repo, device_id, now - timedelta(hours=1), SyncStatus.SUCCESS)
        newer = await _add_session(repo, device_id, now, SyncStatus.FAILED)

        result = await service.list_sessions_for_device(device_id)

        assert [s.id for s in result] == [newer.id, older.id]

    async def test_세션_없는_기기는_빈_목록(self, service: SyncService) -> None:
        result = await service.list_sessions_for_device(uuid.uuid4())
        assert result == []


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
