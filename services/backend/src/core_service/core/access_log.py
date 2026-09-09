"""접속기록 감사로그 — schema.md §5(v1.8), CTO 검토 B5(e),
「개인정보의 안전성 확보조치 기준」제8조(접속기록의 보관 및 점검).

도메인 엔티티가 아니라 순수 인프라 테이블이다(user_encryption_keys와 동일 성격).
`main.py`의 HTTP 미들웨어가 요청 처리 후 best-effort로 1행씩 적재한다 —
적재 실패가 요청을 깨뜨리지 않는다.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, SmallInteger, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from core_service.core.db import Base

_ACTOR_KINDS = ("family_member", "device", "anonymous")


class AccessLogModel(Base):
    __tablename__ = "access_logs"

    id: Mapped[uuid.UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True)
    actor_kind: Mapped[str] = mapped_column(
        SAEnum(*_ACTOR_KINDS, name="access_actor_kind", create_type=False), nullable=False
    )
    actor_subject: Mapped[str | None] = mapped_column(String(255), nullable=True)
    method: Mapped[str] = mapped_column(String(10), nullable=False)
    path: Mapped[str] = mapped_column(String(500), nullable=False)
    status_code: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    client_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AccessLogRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def record(
        self,
        *,
        actor_kind: str,
        actor_subject: str | None,
        method: str,
        path: str,
        status_code: int,
        client_ip: str | None,
    ) -> None:
        self._session.add(
            AccessLogModel(
                id=uuid.uuid4(),
                actor_kind=actor_kind if actor_kind in _ACTOR_KINDS else "anonymous",
                actor_subject=actor_subject,
                method=method,
                path=path[:500],
                status_code=status_code,
                client_ip=client_ip,
                created_at=datetime.now(UTC),
            )
        )
        await self._session.flush()
