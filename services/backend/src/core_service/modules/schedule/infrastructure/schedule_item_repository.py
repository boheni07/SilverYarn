"""schedule_items 테이블 SQLAlchemy 매핑 + Repository — schema.md §5 DDL과 1:1."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, SmallInteger, String, select
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from core_service.core.db import Base
from core_service.modules.schedule.domain.schedule_item import (
    ScheduleItem,
    ScheduleKind,
    ScheduleStatus,
)


class ScheduleItemModel(Base):
    __tablename__ = "schedule_items"

    id: Mapped[uuid.UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    kind: Mapped[str] = mapped_column(
        SAEnum("appointment", "medication", name="schedule_kind", create_type=False),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(String(300), nullable=True)
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    recurrence: Mapped[str | None] = mapped_column(String(50), nullable=True)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(
        SAEnum("pending", "confirmed", "missed", "declined", name="schedule_status", create_type=False),
        nullable=False,
        default="pending",
    )
    remind_count: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    next_remind_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    decline_reason: Mapped[str | None] = mapped_column(String(300), nullable=True)
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def to_domain(self) -> ScheduleItem:
        return ScheduleItem(
            id=self.id,
            user_id=self.user_id,
            kind=ScheduleKind(self.kind),
            description=self.description,
            location=self.location,
            recurrence=self.recurrence,
            due_at=self.due_at,
            status=ScheduleStatus(self.status),
            remind_count=self.remind_count,
            next_remind_at=self.next_remind_at,
            decline_reason=self.decline_reason,
            responded_at=self.responded_at,
        )


class ScheduleItemRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, schedule_item_id: uuid.UUID) -> ScheduleItem | None:
        model = await self._session.get(ScheduleItemModel, schedule_item_id)
        return model.to_domain() if model else None

    async def list_by_user(self, user_id: uuid.UUID) -> list[ScheduleItem]:
        result = await self._session.execute(
            select(ScheduleItemModel)
            .where(ScheduleItemModel.user_id == user_id)
            .order_by(ScheduleItemModel.due_at)
        )
        return [m.to_domain() for m in result.scalars().all()]

    async def create(
        self,
        user_id: uuid.UUID,
        kind: ScheduleKind,
        due_at: datetime,
        description: str | None = None,
        location: str | None = None,
        recurrence: str | None = None,
    ) -> ScheduleItem:
        model = ScheduleItemModel(
            id=uuid.uuid4(),
            user_id=user_id,
            kind=kind.value,
            description=description,
            location=location,
            recurrence=recurrence,
            due_at=due_at,
            status=ScheduleStatus.PENDING.value,
            remind_count=0,
            next_remind_at=None,
            decline_reason=None,
            responded_at=None,
        )
        self._session.add(model)
        await self._session.flush()
        return model.to_domain()

    async def respond(
        self,
        schedule_item_id: uuid.UUID,
        status: ScheduleStatus,
        decline_reason: str | None,
    ) -> ScheduleItem:
        model = await self._session.get(ScheduleItemModel, schedule_item_id)
        if model is None:
            raise LookupError(f"schedule_item {schedule_item_id} not found")
        model.status = status.value
        model.decline_reason = decline_reason
        model.responded_at = datetime.now()
        await self._session.flush()
        return model.to_domain()

    async def schedule_next_reminder(
        self, schedule_item_id: uuid.UUID, next_remind_at: datetime
    ) -> ScheduleItem:
        model = await self._session.get(ScheduleItemModel, schedule_item_id)
        if model is None:
            raise LookupError(f"schedule_item {schedule_item_id} not found")
        model.next_remind_at = next_remind_at
        model.remind_count += 1
        await self._session.flush()
        return model.to_domain()
