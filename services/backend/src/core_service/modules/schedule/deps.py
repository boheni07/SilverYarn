"""schedule 모듈의 공개 조합 지점 — author/deps.py와 동일한 패턴.

sync 모듈의 download()가 ScheduleItemService가 필요할 때 이 파일만 import한다.
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core_service.core.db import get_db
from core_service.modules.schedule.application.schedule_item_service import ScheduleItemService
from core_service.modules.schedule.infrastructure.schedule_item_repository import (
    ScheduleItemRepository,
)


def get_schedule_item_service(session: AsyncSession = Depends(get_db)) -> ScheduleItemService:
    return ScheduleItemService(ScheduleItemRepository(session))
