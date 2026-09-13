"""계정 전체 삭제(erasure) 실행 이력 — decisions.md #56(2026-09-13, Q5), 마이그레이션 0012.

도메인 엔티티가 아니라 순수 인프라 감사 테이블이다(access_logs·user_encryption_keys와
동일 성격). `user_id`가 FK가 아닌 이유: 이 행이 만들어지는 시점엔 그 `users` 행이
막 삭제되려는 참이라(erasure의 마지막 단계) FK를 걸면 항상 위반된다 — 삭제된
뒤에도 "누구를·언제·왜·어디까지 지웠는지" 감사 기록은 남아야 한다.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import ARRAY, DateTime, String
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from core_service.core.db import Base


class DeletionRecordModel(Base):
    __tablename__ = "deletion_records"

    id: Mapped[uuid.UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    requested_by: Mapped[uuid.UUID | None] = mapped_column(PgUUID(as_uuid=True), nullable=True)
    reason: Mapped[str] = mapped_column(String(50), nullable=False)
    purged_stores: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class DeletionRecordRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def record(
        self,
        *,
        user_id: uuid.UUID,
        requested_by: uuid.UUID | None,
        reason: str,
        purged_stores: list[str],
    ) -> None:
        self._session.add(
            DeletionRecordModel(
                id=uuid.uuid4(),
                user_id=user_id,
                requested_by=requested_by,
                reason=reason[:50],
                purged_stores=purged_stores,
                created_at=datetime.now(UTC),
            )
        )
        await self._session.flush()
