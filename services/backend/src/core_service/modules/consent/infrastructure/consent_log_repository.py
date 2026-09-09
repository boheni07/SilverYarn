"""consent_logs 테이블 SQLAlchemy 매핑 + Repository — schema.md §3.14/§5 DDL과 1:1.

불변 로그(append-only) — `update`/`delete` 경로가 없다. 동의 철회도 `granted=false`인
새 행을 만든다.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, select
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from core_service.core.db import Base
from core_service.modules.consent.domain.consent_log import ConsentLog, ConsentType


class ConsentLogModel(Base):
    __tablename__ = "consent_logs"

    id: Mapped[uuid.UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    consent_type: Mapped[str] = mapped_column(
        SAEnum(
            "data_collection",
            "external_tts_optin",
            "external_llm_optin",
            name="consent_type",
            create_type=False,
        ),
        nullable=False,
    )
    granted: Mapped[bool] = mapped_column(Boolean, nullable=False)
    granted_by: Mapped[uuid.UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("family_members.id"), nullable=True
    )
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    def to_domain(self) -> ConsentLog:
        return ConsentLog(
            id=self.id,
            user_id=self.user_id,
            consent_type=ConsentType(self.consent_type),
            granted=self.granted,
            granted_by=self.granted_by,
            granted_at=self.granted_at,
        )


class ConsentLogRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def list_by_user(self, user_id: uuid.UUID) -> list[ConsentLog]:
        result = await self._session.execute(
            select(ConsentLogModel)
            .where(ConsentLogModel.user_id == user_id)
            .order_by(ConsentLogModel.granted_at.desc())
        )
        return [m.to_domain() for m in result.scalars()]

    async def create(
        self,
        user_id: uuid.UUID,
        consent_type: ConsentType,
        granted: bool,
        granted_by: uuid.UUID | None,
    ) -> ConsentLog:
        model = ConsentLogModel(
            id=uuid.uuid4(),
            user_id=user_id,
            consent_type=consent_type.value,
            granted=granted,
            granted_by=granted_by,
            granted_at=datetime.now(UTC),
        )
        self._session.add(model)
        await self._session.flush()
        return model.to_domain()
