"""devices 모듈의 공개 조합 지점 — family_members/deps.py와 동일한 패턴.

sync 모듈이 업로드 요청의 device_id로부터 user_id를 알아내야 할 때 이 파일만
import한다(Device Token이 기기를 가리키고, 기기가 사용자를 가리키는 구조 —
클라이언트가 user_id를 직접 주장하게 하지 않는다).
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core_service.core.db import get_db
from core_service.modules.devices.application.device_service import DeviceService
from core_service.modules.devices.infrastructure.device_repository import DeviceRepository


def get_device_service(session: AsyncSession = Depends(get_db)) -> DeviceService:
    return DeviceService(DeviceRepository(session))
