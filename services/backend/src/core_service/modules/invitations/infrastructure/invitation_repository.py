"""invitations 테이블 SQLAlchemy 매핑 + Repository — schema.md §5 DDL과 1:1."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, select
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

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
    contact: Mapped[str] = mapped_column(String(100), nullable=False)
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

    def to_domain(self) -> Invitation:
        return Invitation(
            id=self.id,
            user_id=self.user_id,
            invited_by=self.invited_by,
            contact=self.contact,
            role=FamilyRole(self.role),
            token=self.token,
            status=InvitationStatus(self.status),
            created_at=self.created_at,
            expires_at=self.expires_at,
        )


class InvitationRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, invitation_id: uuid.UUID) -> Invitation | None:
        model = await self._session.get(InvitationModel, invitation_id)
        return model.to_domain() if model else None

    async def get_by_token(self, token: str) -> Invitation | None:
        result = await self._session.execute(select(InvitationModel).where(InvitationModel.token == token))
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def list_by_user(self, user_id: uuid.UUID) -> list[Invitation]:
        result = await self._session.execute(
            select(InvitationModel)
            .where(InvitationModel.user_id == user_id)
            .order_by(InvitationModel.created_at.desc())
        )
        return [m.to_domain() for m in result.scalars().all()]

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
            contact=contact,
            role=role.value,
            token=token,
            status=InvitationStatus.PENDING.value,
            created_at=datetime.now(),
            expires_at=expires_at,
        )
        self._session.add(model)
        await self._session.flush()
        return model.to_domain()

    async def update_status(self, invitation_id: uuid.UUID, status: InvitationStatus) -> Invitation:
        model = await self._session.get(InvitationModel, invitation_id)
        if model is None:
            raise LookupError(f"invitation {invitation_id} not found")
        model.status = status.value
        await self._session.flush()
        return model.to_domain()
