"""devices 테이블 SQLAlchemy 매핑 + Repository — schema.md §5 DDL과 1:1."""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, select
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from core_service.core.db import Base
from core_service.modules.devices.domain.device import Device, InstallMode


class DeviceModel(Base):
    __tablename__ = "devices"

    id: Mapped[uuid.UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True)
    display_id: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    model_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    ram_gb: Mapped[Decimal] = mapped_column(Numeric(4, 1), nullable=False)
    android_version: Mapped[str] = mapped_column(String(20), nullable=False)
    install_mode: Mapped[str] = mapped_column(
        SAEnum("kiosk", "normal", name="install_mode", create_type=False), nullable=False
    )
    ai_tops: Mapped[Decimal | None] = mapped_column(Numeric(5, 1), nullable=True)
    slm_model_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    prompt_pack_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    installed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def to_domain(self) -> Device:
        return Device(
            id=self.id,
            display_id=self.display_id,
            model_name=self.model_name,
            user_id=self.user_id,
            ram_gb=self.ram_gb,
            android_version=self.android_version,
            install_mode=InstallMode(self.install_mode),
            ai_tops=self.ai_tops,
            slm_model_version=self.slm_model_version,
            prompt_pack_version=self.prompt_pack_version,
            installed_at=self.installed_at,
            last_sync_at=self.last_sync_at,
        )


class DeviceRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, device_id: uuid.UUID) -> Device | None:
        model = await self._session.get(DeviceModel, device_id)
        return model.to_domain() if model else None

    async def list_by_user(self, user_id: uuid.UUID) -> list[Device]:
        result = await self._session.execute(select(DeviceModel).where(DeviceModel.user_id == user_id))
        return [m.to_domain() for m in result.scalars().all()]

    async def create(
        self,
        display_id: str,
        model_name: str | None,
        user_id: uuid.UUID,
        ram_gb: Decimal,
        android_version: str,
        install_mode: InstallMode,
    ) -> Device:
        model = DeviceModel(
            id=uuid.uuid4(),
            display_id=display_id,
            model_name=model_name,
            user_id=user_id,
            ram_gb=ram_gb,
            android_version=android_version,
            install_mode=install_mode.value,
            ai_tops=None,
            slm_model_version=None,
            prompt_pack_version=None,
            installed_at=datetime.now(),
            last_sync_at=None,
        )
        self._session.add(model)
        await self._session.flush()
        return model.to_domain()
