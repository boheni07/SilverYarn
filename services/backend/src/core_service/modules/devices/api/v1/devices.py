"""devices 리소스 라우터.

design.md §4.2 M-8 정정: `/devices/{userId}` → `/users/{userId}/devices`(소유자 중첩 규칙).
등록(`POST /devices`)은 설치 트리거성 엔드포인트라 예외로 중첩하지 않는다(F-3 예외 규칙).

`POST /devices`는 토큰이 아직 없는 부트스트랩 호출이라 인증하지 않는다(원본 흐름도 §3.6
프로비저닝). 대신 이 호출의 응답으로 **Device Token을 1회 발급**한다(decisions.md #47) —
이후 모든 `/sync/*` 호출은 이 토큰을 `X-Device-Token`으로 제시해야 한다.
"""

import uuid
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core_service.core.auth import require_roles
from core_service.core.db import get_db
from core_service.modules.devices.application.device_service import DeviceService
from core_service.modules.devices.infrastructure.device_credential_repository import (
    DeviceCredentialRepository,
)
from core_service.modules.devices.infrastructure.device_repository import DeviceRepository
from core_service.shared.domain_enums import FamilyRole
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


class DeviceRegisteredResponse(DeviceResponse):
    # 발급 즉시 1회만 응답에 담긴다 — 서버는 해시만 보관하므로 이후 재조회 불가.
    device_token: str


def _service(session: AsyncSession = Depends(get_db)) -> DeviceService:
    return DeviceService(DeviceRepository(session))


def _device_fields(device) -> dict:  # noqa: ANN001 — Device 도메인 dataclass
    return {**device.__dict__, "install_mode": device.install_mode.value}


@router.post("/devices", response_model=DataResponse[DeviceRegisteredResponse], status_code=201)
async def register_device(
    body: DeviceRegisterRequest,
    service: DeviceService = Depends(_service),
    session: AsyncSession = Depends(get_db),
) -> DataResponse[DeviceRegisteredResponse]:
    """설치 시점 1회 기기 등록 — install_mode는 서버가 decisions.md #5로 판정하고,
    Device Token(decisions.md #47)을 함께 발급한다."""
    device = await service.register_device(
        display_id=body.display_id,
        model_name=body.model_name,
        user_id=body.user_id,
        ram_gb=body.ram_gb,
        android_version=body.android_version,
    )
    token = await DeviceCredentialRepository(session).issue(device.id)
    return DataResponse(data=DeviceRegisteredResponse(**_device_fields(device), device_token=token))


@router.get("/users/{user_id}/devices", response_model=DataResponse[list[DeviceResponse]])
async def list_user_devices(
    user_id: uuid.UUID,
    service: DeviceService = Depends(_service),
    _admin=Depends(require_roles(FamilyRole.ADMIN)),  # noqa: ANN001 — design.md §7.1 기기 관리 = admin 전용
) -> DataResponse[list[DeviceResponse]]:
    devices = await service.list_devices_for_user(user_id)
    return DataResponse(data=[DeviceResponse(**_device_fields(d)) for d in devices])
