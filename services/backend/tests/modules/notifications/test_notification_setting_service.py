"""NotificationSettingService 유닛 테스트 — 페이크 Repository로 DB 없이 검증."""

import uuid
from datetime import UTC, datetime

import pytest

from core_service.core.errors import ApiError
from core_service.modules.notifications.application.notification_setting_service import (
    ChannelPreference,
    NotificationSettingService,
)
from core_service.modules.notifications.domain.notification_setting import (
    NotificationSetting,
    NotifyChannel,
)


class FakeNotificationSettingRepository:
    def __init__(self) -> None:
        self._store: dict[uuid.UUID, list[NotificationSetting]] = {}

    async def list_by_family_member(self, family_member_id: uuid.UUID) -> list[NotificationSetting]:
        return list(self._store.get(family_member_id, []))

    async def replace_for_family_member(
        self, family_member_id: uuid.UUID, settings: list[NotificationSetting]
    ) -> list[NotificationSetting]:
        stored = [
            NotificationSetting(
                id=uuid.uuid4(),  # repository가 새로 발급
                family_member_id=family_member_id,
                channel=s.channel,
                receives_emotion_alerts=s.receives_emotion_alerts,
                receives_chapter_updates=s.receives_chapter_updates,
                receives_sync_issues=s.receives_sync_issues,
                updated_at=datetime.now(UTC),
            )
            for s in settings
        ]
        self._store[family_member_id] = stored
        return list(stored)


@pytest.fixture
def repo() -> FakeNotificationSettingRepository:
    return FakeNotificationSettingRepository()


@pytest.fixture
def service(repo: FakeNotificationSettingRepository) -> NotificationSettingService:
    return NotificationSettingService(repo)  # type: ignore[arg-type]


def _pref(channel: NotifyChannel, *, emotion: bool = False) -> ChannelPreference:
    return ChannelPreference(
        channel=channel,
        receives_emotion_alerts=emotion,
        receives_chapter_updates=True,
        receives_sync_issues=False,
    )


async def test_replace_then_get_roundtrip(service: NotificationSettingService) -> None:
    fm_id = uuid.uuid4()
    result = await service.replace_settings(
        fm_id, [_pref(NotifyChannel.PUSH), _pref(NotifyChannel.EMAIL, emotion=True)]
    )
    assert {s.channel for s in result} == {NotifyChannel.PUSH, NotifyChannel.EMAIL}
    assert next(s for s in result if s.channel == NotifyChannel.EMAIL).receives_emotion_alerts is True

    fetched = await service.get_settings(fm_id)
    assert {s.channel for s in fetched} == {NotifyChannel.PUSH, NotifyChannel.EMAIL}


async def test_replace_is_full_replacement(service: NotificationSettingService) -> None:
    fm_id = uuid.uuid4()
    await service.replace_settings(fm_id, [_pref(NotifyChannel.PUSH), _pref(NotifyChannel.SMS)])
    await service.replace_settings(fm_id, [_pref(NotifyChannel.EMAIL)])

    fetched = await service.get_settings(fm_id)
    assert [s.channel for s in fetched] == [NotifyChannel.EMAIL]


async def test_duplicate_channel_rejected(service: NotificationSettingService) -> None:
    with pytest.raises(ApiError) as exc:
        await service.replace_settings(uuid.uuid4(), [_pref(NotifyChannel.PUSH), _pref(NotifyChannel.PUSH)])
    assert exc.value.code == "VALIDATION_ERROR"


async def test_empty_replacement_clears_all(service: NotificationSettingService) -> None:
    fm_id = uuid.uuid4()
    await service.replace_settings(fm_id, [_pref(NotifyChannel.PUSH)])
    await service.replace_settings(fm_id, [])
    assert await service.get_settings(fm_id) == []


async def test_get_settings_empty_by_default(service: NotificationSettingService) -> None:
    assert await service.get_settings(uuid.uuid4()) == []
