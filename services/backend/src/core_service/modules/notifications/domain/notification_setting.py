"""NotificationSetting 도메인 엔티티 — schema.md §3.15 `notification_settings` 매핑.

WF5 화면의 "수신 대상·채널 선택" — **이미 발생한 알림을 누가·어떤 채널로 받을지**만
다룬다. 알림을 보낼지 말지의 임계치 로직(정서 모니터링 등)은 이 범위 밖이며
decisions.md #12(법무검토 대기)와 충돌하지 않도록 의도적으로 제한됨.

한 family_member는 채널(sms/email/push)마다 최대 1개 설정을 가진다
(마이그레이션 0005의 `uq_notification_settings_member_channel`).
"""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class NotifyChannel(StrEnum):
    SMS = "sms"
    EMAIL = "email"
    PUSH = "push"


@dataclass
class NotificationSetting:
    id: UUID
    family_member_id: UUID
    channel: NotifyChannel
    receives_emotion_alerts: bool
    receives_chapter_updates: bool
    receives_sync_issues: bool
    updated_at: datetime
