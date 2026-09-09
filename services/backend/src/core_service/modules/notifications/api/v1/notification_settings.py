"""notification_settings 리소스 라우터 — design.md §4.2 `PUT /family-members/{id}/notification-settings`.

WF5 "알림·가족구성원 설정" 화면. 조회(GET)는 그 화면을 그리려면 필요해 함께 둔다.
인가: 본인의 구성원 설정만(design.md §7.1 "본인 것만"), admin은 전체. 2FA 필수.
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from core_service.core.auth import AuthContext, authorize_own_family_member, require_auth
from core_service.modules.notifications.application.notification_setting_service import (
    ChannelPreference,
    NotificationSettingService,
)
from core_service.modules.notifications.deps import get_notification_setting_service
from core_service.modules.notifications.domain.notification_setting import NotificationSetting, NotifyChannel
from core_service.shared.schemas import DataResponse

router = APIRouter(prefix="/family-members/{family_member_id}", tags=["notification-settings"])


class ChannelPreferencePayload(BaseModel):
    channel: NotifyChannel
    # 정서 알림 기본 opt-out(CTO 검토 B1 — 민감정보 인접 알림은 opt-in이어야 함).
    receives_emotion_alerts: bool = False
    receives_chapter_updates: bool = True
    receives_sync_issues: bool = False


class NotificationSettingsReplaceRequest(BaseModel):
    settings: list[ChannelPreferencePayload]


class NotificationSettingResponse(BaseModel):
    id: uuid.UUID
    family_member_id: uuid.UUID
    channel: str
    receives_emotion_alerts: bool
    receives_chapter_updates: bool
    receives_sync_issues: bool
    updated_at: datetime


def _to_response(setting: NotificationSetting) -> NotificationSettingResponse:
    return NotificationSettingResponse(
        id=setting.id,
        family_member_id=setting.family_member_id,
        channel=setting.channel.value,
        receives_emotion_alerts=setting.receives_emotion_alerts,
        receives_chapter_updates=setting.receives_chapter_updates,
        receives_sync_issues=setting.receives_sync_issues,
        updated_at=setting.updated_at,
    )


@router.get(
    "/notification-settings",
    response_model=DataResponse[list[NotificationSettingResponse]],
)
async def get_notification_settings(
    family_member_id: uuid.UUID,
    service: NotificationSettingService = Depends(get_notification_setting_service),
    ctx: AuthContext = Depends(require_auth),
) -> DataResponse[list[NotificationSettingResponse]]:
    authorize_own_family_member(ctx, family_member_id)
    settings = await service.get_settings(family_member_id)
    return DataResponse(data=[_to_response(s) for s in settings])


@router.put(
    "/notification-settings",
    response_model=DataResponse[list[NotificationSettingResponse]],
)
async def replace_notification_settings(
    family_member_id: uuid.UUID,
    body: NotificationSettingsReplaceRequest,
    service: NotificationSettingService = Depends(get_notification_setting_service),
    ctx: AuthContext = Depends(require_auth),
) -> DataResponse[list[NotificationSettingResponse]]:
    """design.md §4.2 — 알림 수신 채널·항목 설정. 이 구성원의 설정 전체를 통째로 교체(PUT)."""
    authorize_own_family_member(ctx, family_member_id)
    preferences = [
        ChannelPreference(
            channel=p.channel,
            receives_emotion_alerts=p.receives_emotion_alerts,
            receives_chapter_updates=p.receives_chapter_updates,
            receives_sync_issues=p.receives_sync_issues,
        )
        for p in body.settings
    ]
    settings = await service.replace_settings(family_member_id, preferences)
    return DataResponse(data=[_to_response(s) for s in settings])
