"""invitations 테이블 SQLAlchemy 매핑 + Repository — schema.md §5 DDL과 1:1.

`contact`는 PII 암호화 대상(decisions.md #45 2차) — 암호문 저장, 소유 어르신 DEK로
암복호화. `contact_bidx`(HMAC hex)로 "같은 사람에게 이미 대기 중인 초대가 있는지"를
동등검색한다(중복 초대 방지).
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String, select
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from core_service.core.crypto import PiiFieldEncryptor, get_pii_encryptor
from core_service.core.db import Base
from core_service.modules.invitations.domain.invitation import Invitation, InvitationStatus
from core_service.shared.domain_enums import FamilyRole


class InvitationModel(Base):
    __tablename__ = "invitations"

    id: Mapped[uuid.UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    invited_by: Mapped[uuid.UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("family_members.id"), nullable=True
    )
    contact: Mapped[str] = mapped_column(String(255), nullable=False)  # 저장 시 암호문
    contact_bidx: Mapped[str | None] = mapped_column(String(64), nullable=True)  # HMAC hex
    role: Mapped[str] = mapped_column(
        SAEnum("family", "caregiver", "social_worker", "admin", name="family_role", create_type=False),
        nullable=False,
    )
    token: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(
        SAEnum("pending", "accepted", "expired", name="invitation_status", create_type=False),
        nullable=False,
        default="pending",
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class InvitationRepository:
    def __init__(self, session: AsyncSession, pii: PiiFieldEncryptor | None = None):
        self._session = session
        self._pii = pii or get_pii_encryptor()

    async def _to_domain(self, model: InvitationModel) -> Invitation:
        return Invitation(
            id=model.id,
            user_id=model.user_id,
            invited_by=model.invited_by,
            contact=await self._pii.decrypt(self._session, model.user_id, model.contact),
            role=FamilyRole(model.role),
            token=model.token,
            status=InvitationStatus(model.status),
            created_at=model.created_at,
            expires_at=model.expires_at,
        )

    async def get_by_id(self, invitation_id: uuid.UUID) -> Invitation | None:
        model = await self._session.get(InvitationModel, invitation_id)
        return await self._to_domain(model) if model else None

    async def get_by_token(self, token: str) -> Invitation | None:
        result = await self._session.execute(select(InvitationModel).where(InvitationModel.token == token))
        model = result.scalar_one_or_none()
        return await self._to_domain(model) if model else None

    async def list_by_user(self, user_id: uuid.UUID) -> list[Invitation]:
        result = await self._session.execute(
            select(InvitationModel)
            .where(InvitationModel.user_id == user_id)
            .order_by(InvitationModel.created_at.desc())
        )
        return [await self._to_domain(m) for m in result.scalars().all()]

    async def exists_pending_for_contact(self, user_id: uuid.UUID, contact: str) -> bool:
        """이 어르신 계정에, 같은 연락처로 아직 대기 중인 초대가 있는가 (중복 초대 방지)."""
        result = await self._session.execute(
            select(InvitationModel.id).where(
                InvitationModel.user_id == user_id,
                InvitationModel.contact_bidx == self._pii.blind_index(contact),
                InvitationModel.status == InvitationStatus.PENDING.value,
            )
        )
        return result.first() is not None

    async def create(
        self,
        user_id: uuid.UUID,
        invited_by: uuid.UUID | None,
        contact: str,
        role: FamilyRole,
        token: str,
        expires_at: datetime,
    ) -> Invitation:
        model = InvitationModel(
            id=uuid.uuid4(),
            user_id=user_id,
            invited_by=invited_by,
            contact=await self._pii.encrypt(self._session, user_id, contact),
            contact_bidx=self._pii.blind_index(contact),
            role=role.value,
            token=token,
            status=InvitationStatus.PENDING.value,
            created_at=datetime.now(UTC),
            expires_at=expires_at,
        )
        self._session.add(model)
        await self._session.flush()
        return await self._to_domain(model)

    async def update_status(self, invitation_id: uuid.UUID, status: InvitationStatus) -> Invitation:
        model = await self._session.get(InvitationModel, invitation_id)
        if model is None:
            raise LookupError(f"invitation {invitation_id} not found")
        model.status = status.value
        await self._session.flush()
        return await self._to_domain(model)
