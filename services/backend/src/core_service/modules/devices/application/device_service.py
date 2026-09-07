"""Device 유스케이스."""

import uuid
from decimal import Decimal

from core_service.core.errors import ApiError
from core_service.modules.devices.domain.device import Device, determine_install_mode
from core_service.modules.devices.infrastructure.device_repository import DeviceRepository


class DeviceService:
    def __init__(self, repo: DeviceRepository):
        self._repo = repo

    async def list_devices_for_user(self, user_id: uuid.UUID) -> list[Device]:
        return await self._repo.list_by_user(user_id)

    async def get_device(self, device_id: uuid.UUID) -> Device:
        device = await self._repo.get_by_id(device_id)
        if device is None:
            raise ApiError("NOT_FOUND", f"기기({device_id})를 찾을 수 없습니다.")
        return device

    async def register_device(
        self,
        display_id: str,
        model_name: str | None,
        user_id: uuid.UUID,
        ram_gb: Decimal,
        android_version: str,
    ) -> Device:
        """설치 시점 1회 등록 — install_mode는 decisions.md #5 임계값으로 서버가 판정."""
        install_mode = determine_install_mode(ram_gb, android_version)
        return await self._repo.create(
            display_id=display_id,
            model_name=model_name,
            user_id=user_id,
            ram_gb=ram_gb,
            android_version=android_version,
            install_mode=install_mode,
        )
