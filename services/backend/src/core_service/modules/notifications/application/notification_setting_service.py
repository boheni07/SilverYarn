"""NotificationSetting 유스케이스 — WF5 알림 수신 설정."""

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from core_service.core.errors import ApiError
from core_service.modules.notifications.domain.notification_setting import (
    NotificationSetting,
    NotifyChannel,
)
from core_service.modules.notifications.infrastructure.notification_setting_repository import (
    NotificationSettingRepository,
)


@dataclass
class ChannelPreference:
    """PUT 요청 1건 — 한 채널의 수신 항목 스위치."""

    channel: NotifyChannel
    receives_emotion_alerts: bool
    receives_chapter_updates: bool
    receives_sync_issues: bool


class NotificationSettingService:
    def __init__(self, repo: NotificationSettingRepository):
        self._repo = repo

    async def get_settings(self, family_member_id: uuid.UUID) -> list[NotificationSetting]:
        return await self._repo.list_by_family_member(family_member_id)

    async def replace_settings(
        self, family_member_id: uuid.UUID, preferences: list[ChannelPreference]
    ) -> list[NotificationSetting]:
        seen: set[NotifyChannel] = set()
        for pref in preferences:
            if pref.channel in seen:
                raise ApiError("VALIDATION_ERROR", f"채널 '{pref.channel.value}'이 중복됐습니다.")
            seen.add(pref.channel)

        # id/updated_at은 repository가 저장 시점에 발급/설정한다 — 여기 값은 무시된다.
        placeholder_ts = datetime.now(UTC)
        settings = [
            NotificationSetting(
                id=uuid.uuid4(),
                family_member_id=family_member_id,
                channel=pref.channel,
                receives_emotion_alerts=pref.receives_emotion_alerts,
                receives_chapter_updates=pref.receives_chapter_updates,
                receives_sync_issues=pref.receives_sync_issues,
                updated_at=placeholder_ts,
            )
            for pref in preferences
        ]
        return await self._repo.replace_for_family_member(family_member_id, settings)
