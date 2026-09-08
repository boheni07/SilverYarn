"""DeviceService 유닛 테스트 — 페이크 Repository로 DB 없이 Application 계층 검증.

핵심 검증 대상: get_display_ids()가 apps/admin 전체 기기 통합 모니터링 화면에서
sync_sessions.device_id 목록을 device_id → display_id 매핑으로 정확히 바꿔 주는지 —
이 메서드가 sync 모듈이 devices 테이블을 직접 조인하지 않고도 기기 표시명을
붙이는 유일한 통로다(services/sync/api/v1/sync.py list_sessions).
"""

import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from core_service.modules.devices.application.device_service import DeviceService
from core_service.modules.devices.domain.device import Device, InstallMode


class FakeDeviceRepository:
    def __init__(self) -> None:
        self._store: dict[uuid.UUID, Device] = {}

    def _add(self, display_id: str) -> Device:
        device = Device(
            id=uuid.uuid4(),
            display_id=display_id,
            model_name=None,
            user_id=uuid.uuid4(),
            ram_gb=Decimal("4.0"),
            android_version="12",
            install_mode=InstallMode.KIOSK,
            ai_tops=None,
            slm_model_version=None,
            prompt_pack_version=None,
            installed_at=datetime.now(UTC),
            last_sync_at=None,
        )
        self._store[device.id] = device
        return device

    async def get_by_id(self, device_id: uuid.UUID) -> Device | None:
        return self._store.get(device_id)

    async def list_by_user(self, user_id: uuid.UUID) -> list[Device]:
        return [d for d in self._store.values() if d.user_id == user_id]

    async def list_by_ids(self, device_ids: list[uuid.UUID]) -> list[Device]:
        wanted = set(device_ids)
        return [d for d in self._store.values() if d.id in wanted]


@pytest.fixture
def repo() -> FakeDeviceRepository:
    return FakeDeviceRepository()


@pytest.fixture
def service(repo: FakeDeviceRepository) -> DeviceService:
    return DeviceService(repo)  # type: ignore[arg-type]


class TestGetDisplayIds:
    async def test_요청한_기기들의_display_id를_매핑으로_반환(
        self, service: DeviceService, repo: FakeDeviceRepository
    ) -> None:
        device_a = repo._add("MB-1001")
        device_b = repo._add("MB-1002")
        repo._add("MB-1003")  # 요청에 없는 기기 — 결과에 안 나와야 함

        result = await service.get_display_ids([device_a.id, device_b.id])

        assert result == {device_a.id: "MB-1001", device_b.id: "MB-1002"}

    async def test_빈_목록이면_빈_매핑(self, service: DeviceService) -> None:
        assert await service.get_display_ids([]) == {}

    async def test_존재하지_않는_기기_ID는_매핑에서_빠짐(
        self, service: DeviceService, repo: FakeDeviceRepository
    ) -> None:
        # 삭제된 기기(FK CASCADE)의 sync_session이 남아 있는 경우를 흉내
        result = await service.get_display_ids([uuid.uuid4()])
        assert result == {}
