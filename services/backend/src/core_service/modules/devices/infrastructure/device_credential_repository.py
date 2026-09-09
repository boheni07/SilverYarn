"""device_credentials 테이블 SQLAlchemy 매핑 + Repository — schema.md §5(v1.8), decisions.md #47.

CTO 검토 B5(b): Device Token 발급·회전·폐기. 평문 토큰은 발급 시 1회만 응답에 담고
서버는 SHA-256 해시(`token_hash`)만 보관한다 — DB가 유출돼도 토큰을 복원할 수 없다.
"""

import hashlib
import secrets
import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String, select
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from core_service.core.auth import DeviceIdentity
from core_service.core.db import Base


class DeviceCredentialModel(Base):
    __tablename__ = "device_credentials"

    id: Mapped[uuid.UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True)
    device_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


def hash_token(plaintext: str) -> str:
    return hashlib.sha256(plaintext.encode()).hexdigest()


class DeviceCredentialRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def issue(self, device_id: uuid.UUID) -> str:
        """새 토큰을 발급하고 해시를 저장한 뒤 **평문 토큰**을 돌려준다(호출자가 1회만 노출)."""
        plaintext = secrets.token_urlsafe(32)
        model = DeviceCredentialModel(
            id=uuid.uuid4(),
            device_id=device_id,
            token_hash=hash_token(plaintext),
            issued_at=datetime.now(UTC),
        )
        self._session.add(model)
        await self._session.flush()
        return plaintext

    async def resolve_active(self, token_hash: str) -> DeviceIdentity | None:
        """폐기되지 않은 자격증명을 찾아 (device_id, 소속 어르신 user_id)를 돌려준다.

        devices 테이블을 조인해 user_id까지 한 번에 얻는다 — core/auth.py의 require_device가
        DeviceIdentity(device_id, user_id)를 필요로 하기 때문(sync-contract.md v0.3에서
        device_id로 device→user_id 신뢰사슬을 쓰던 것을 여기로 옮겨 정식화).
        """
        from core_service.modules.devices.infrastructure.device_repository import DeviceModel

        row = (
            await self._session.execute(
                select(DeviceCredentialModel, DeviceModel.user_id)
                .join(DeviceModel, DeviceModel.id == DeviceCredentialModel.device_id)
                .where(
                    DeviceCredentialModel.token_hash == token_hash,
                    DeviceCredentialModel.revoked_at.is_(None),
                )
            )
        ).first()
        if row is None:
            return None
        credential, user_id = row
        credential.last_used_at = datetime.now(UTC)
        await self._session.flush()
        return DeviceIdentity(device_id=credential.device_id, user_id=user_id)

    async def revoke_all_for_device(self, device_id: uuid.UUID) -> int:
        """분실·재프로비저닝 시 해당 기기의 모든 활성 토큰을 폐기."""
        rows = (
            (
                await self._session.execute(
                    select(DeviceCredentialModel).where(
                        DeviceCredentialModel.device_id == device_id,
                        DeviceCredentialModel.revoked_at.is_(None),
                    )
                )
            )
            .scalars()
            .all()
        )
        now = datetime.now(UTC)
        for row in rows:
            row.revoked_at = now
        await self._session.flush()
        return len(rows)
