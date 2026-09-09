"""notifications 모듈의 공개 조합 지점."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core_service.core.db import get_db
from core_service.modules.notifications.application.notification_setting_service import (
    NotificationSettingService,
)
from core_service.modules.notifications.infrastructure.notification_setting_repository import (
    NotificationSettingRepository,
)


def get_notification_setting_service(
    session: AsyncSession = Depends(get_db),
) -> NotificationSettingService:
    return NotificationSettingService(NotificationSettingRepository(session))
