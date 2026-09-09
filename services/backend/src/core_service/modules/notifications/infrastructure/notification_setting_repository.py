"""notification_settings 테이블 SQLAlchemy 매핑 + Repository — schema.md §3.15/§5 DDL과 1:1."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, delete, select
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from core_service.core.db import Base
from core_service.modules.notifications.domain.notification_setting import (
    NotificationSetting,
    NotifyChannel,
)


class NotificationSettingModel(Base):
    __tablename__ = "notification_settings"

    id: Mapped[uuid.UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True)
    family_member_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("family_members.id", ondelete="CASCADE"), nullable=False
    )
    channel: Mapped[str] = mapped_column(
        SAEnum("sms", "email", "push", name="notify_channel", create_type=False), nullable=False
    )
    receives_emotion_alerts: Mapped[bool] = mapped_column(Boolean, nullable=False)
    receives_chapter_updates: Mapped[bool] = mapped_column(Boolean, nullable=False)
    receives_sync_issues: Mapped[bool] = mapped_column(Boolean, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    def to_domain(self) -> NotificationSetting:
        return NotificationSetting(
            id=self.id,
            family_member_id=self.family_member_id,
            channel=NotifyChannel(self.channel),
            receives_emotion_alerts=self.receives_emotion_alerts,
            receives_chapter_updates=self.receives_chapter_updates,
            receives_sync_issues=self.receives_sync_issues,
            updated_at=self.updated_at,
        )


class NotificationSettingRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def list_by_family_member(self, family_member_id: uuid.UUID) -> list[NotificationSetting]:
        result = await self._session.execute(
            select(NotificationSettingModel)
            .where(NotificationSettingModel.family_member_id == family_member_id)
            .order_by(NotificationSettingModel.channel)
        )
        return [m.to_domain() for m in result.scalars().all()]

    async def replace_for_family_member(
        self, family_member_id: uuid.UUID, settings: list[NotificationSetting]
    ) -> list[NotificationSetting]:
        """이 구성원의 설정 전체를 통째로 교체한다(PUT 시맨틱). 같은 트랜잭션 안에서
        delete → insert하므로 채널별 UNIQUE 제약과 충돌하지 않는다."""
        await self._session.execute(
            delete(NotificationSettingModel).where(
                NotificationSettingModel.family_member_id == family_member_id
            )
        )
        now = datetime.now(UTC)
        for setting in settings:
            self._session.add(
                NotificationSettingModel(
                    id=uuid.uuid4(),
                    family_member_id=family_member_id,
                    channel=setting.channel.value,
                    receives_emotion_alerts=setting.receives_emotion_alerts,
                    receives_chapter_updates=setting.receives_chapter_updates,
                    receives_sync_issues=setting.receives_sync_issues,
                    updated_at=now,
                )
            )
        await self._session.flush()
        return await self.list_by_family_member(family_member_id)
