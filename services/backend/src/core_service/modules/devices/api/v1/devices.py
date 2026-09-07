"""devices 리소스 라우터.

design.md §4.2 M-8 정정: `/devices/{userId}` → `/users/{userId}/devices`(소유자 중첩 규칙).
등록(`POST /devices`)은 설치 트리거성 엔드포인트라 예외로 중첩하지 않는다(F-3 예외 규칙).
"""

import uuid
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core_service.core.auth import AuthContext, require_auth
from core_service.core.db import get_db
from core_service.modules.devices.application.device_service import DeviceService
from core_service.modules.devices.infrastructure.device_repository import DeviceRepository
from core_service.shared.schemas import DataResponse

router = APIRouter(tags=["devices"])


class DeviceRegisterRequest(BaseModel):
    display_id: str
    model_name: str | None = None
    user_id: uuid.UUID
    ram_gb: Decimal
    android_version: str


class DeviceResponse(BaseModel):
    id: uuid.UUID
    display_id: str
    model_name: str | None
    user_id: uuid.UUID
    ram_gb: Decimal
    android_version: str
    install_mode: str
    ai_tops: Decimal | None
    slm_model_version: str | None
    prompt_pack_version: str | None
    installed_at: datetime
    last_sync_at: datetime | None


def _service(session: AsyncSession = Depends(get_db)) -> DeviceService:
    return DeviceService(DeviceRepository(session))


@router.post("/devices", response_model=DataResponse[DeviceResponse], status_code=201)
async def register_device(
    body: DeviceRegisterRequest,
    service: DeviceService = Depends(_service),
) -> DataResponse[DeviceResponse]:
    """설치 시점 1회 기기 등록 — install_mode는 서버가 decisions.md #5로 판정."""
    device = await service.register_device(
        display_id=body.display_id,
        model_name=body.model_name,
        user_id=body.user_id,
        ram_gb=body.ram_gb,
        android_version=body.android_version,
    )
    return DataResponse(data=DeviceResponse(**{**device.__dict__, "install_mode": device.install_mode.value}))


@router.get("/users/{user_id}/devices", response_model=DataResponse[list[DeviceResponse]])
async def list_user_devices(
    user_id: uuid.UUID,
    service: DeviceService = Depends(_service),
    _ctx: AuthContext = Depends(require_auth),  # Admin — TODO: role 체크 강화
) -> DataResponse[list[DeviceResponse]]:
    devices = await service.list_devices_for_user(user_id)
    return DataResponse(
        data=[DeviceResponse(**{**d.__dict__, "install_mode": d.install_mode.value}) for d in devices]
    )
