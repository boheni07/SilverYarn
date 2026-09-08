"""sync_sessions 테이블 SQLAlchemy 매핑 + Repository — schema.md §5 DDL과 1:1."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func, select
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from core_service.core.db import Base
from core_service.modules.sync.domain.sync_session import SyncDirection, SyncSession, SyncStatus


class SyncSessionModel(Base):
    __tablename__ = "sync_sessions"

    id: Mapped[uuid.UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True)
    device_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False
    )
    direction: Mapped[str] = mapped_column(
        SAEnum("upload", "download", name="sync_direction", create_type=False), nullable=False
    )
    status: Mapped[str] = mapped_column(
        SAEnum("success", "failed", "retrying", name="sync_status", create_type=False),
        nullable=False,
    )
    checksum: Mapped[str] = mapped_column(String(128), nullable=False)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def to_domain(self) -> SyncSession:
        return SyncSession(
            id=self.id,
            device_id=self.device_id,
            direction=SyncDirection(self.direction),
            status=SyncStatus(self.status),
            checksum=self.checksum,
            retry_count=self.retry_count,
            started_at=self.started_at,
            finished_at=self.finished_at,
        )


class SyncSessionRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, session_id: uuid.UUID) -> SyncSession | None:
        model = await self._session.get(SyncSessionModel, session_id)
        return model.to_domain() if model else None

    async def list_all(
        self,
        offset: int,
        limit: int,
        device_id: uuid.UUID | None = None,
        status: SyncStatus | None = None,
    ) -> tuple[list[SyncSession], int]:
        """apps/admin 동기화 모니터링 화면(기기별 조회·전체 기기 통합 모니터링)의 공통
        조회 경로 — device_id를 주면 기존 idx_sync_device(device_id, started_at DESC)를,
        생략하면(전체 기기 통합 모니터링) idx_sync_started_at(started_at DESC, schema.md
        v1.5 신규)을 쓴다. status 필터는 운영자가 "지금 실패/재시도중인 것만" 훑어보는
        용도 — UserRepository.list_all()과 동일한 페이지네이션 계약.
        """
        count_stmt = select(func.count()).select_from(SyncSessionModel)
        list_stmt = select(SyncSessionModel).order_by(SyncSessionModel.started_at.desc())
        if device_id is not None:
            count_stmt = count_stmt.where(SyncSessionModel.device_id == device_id)
            list_stmt = list_stmt.where(SyncSessionModel.device_id == device_id)
        if status is not None:
            count_stmt = count_stmt.where(SyncSessionModel.status == status.value)
            list_stmt = list_stmt.where(SyncSessionModel.status == status.value)

        total = (await self._session.execute(count_stmt)).scalar_one()
        result = await self._session.execute(list_stmt.offset(offset).limit(limit))
        sessions = [model.to_domain() for model in result.scalars()]
        return sessions, total

    async def create(self, device_id: uuid.UUID, direction: SyncDirection, checksum: str) -> SyncSession:
        model = SyncSessionModel(
            id=uuid.uuid4(),
            device_id=device_id,
            direction=direction.value,
            status=SyncStatus.RETRYING.value,  # 잡 큐 등록 직후 상태 — worker가 처리 후 갱신
            checksum=checksum,
            retry_count=0,
            started_at=datetime.now(UTC),
            finished_at=None,
        )
        self._session.add(model)
        await self._session.flush()
        return model.to_domain()

    async def update_status(
        self, session_id: uuid.UUID, status: SyncStatus, increment_retry: bool = False
    ) -> SyncSession:
        """UploadPipelineService가 파이프라인 종료 시 호출 — success/failed는 종결
        상태라 finished_at을 찍고, retrying으로 되돌아갈 때만 finished_at을 남기지
        않는다(아직 끝나지 않았으므로)."""
        model = await self._session.get(SyncSessionModel, session_id)
        if model is None:
            raise LookupError(f"sync_session {session_id} not found")
        model.status = status.value
        if increment_retry:
            model.retry_count += 1
        if status in (SyncStatus.SUCCESS, SyncStatus.FAILED):
            model.finished_at = datetime.now(UTC)
        await self._session.flush()
        return model.to_domain()
