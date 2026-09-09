"""family_members 테이블 SQLAlchemy 매핑 + Repository — schema.md §5 DDL과 1:1."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, select
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from core_service.core.db import Base
from core_service.modules.family_members.domain.family_member import FamilyMember, FamilyRole


class FamilyMemberModel(Base):
    __tablename__ = "family_members"

    id: Mapped[uuid.UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(
        SAEnum("family", "caregiver", "social_worker", "admin", name="family_role", create_type=False),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    contact: Mapped[str] = mapped_column(String(100), nullable=False)
    two_factor_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Keycloak 토큰 sub ↔ DB 행 매핑 (decisions.md #47, 마이그레이션 0003). 비유일 —
    # 한 사람이 여러 어르신을 담당하면 같은 sub로 여러 행이 생긴다.
    keycloak_sub: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    def to_domain(self) -> FamilyMember:
        return FamilyMember(
            id=self.id,
            user_id=self.user_id,
            role=FamilyRole(self.role),
            name=self.name,
            contact=self.contact,
            two_factor_enabled=self.two_factor_enabled,
            keycloak_sub=self.keycloak_sub,
            created_at=self.created_at,
        )


class FamilyMemberRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, family_member_id: uuid.UUID) -> FamilyMember | None:
        model = await self._session.get(FamilyMemberModel, family_member_id)
        return model.to_domain() if model else None

    async def list_by_user(self, user_id: uuid.UUID) -> list[FamilyMember]:
        result = await self._session.execute(
            select(FamilyMemberModel)
            .where(FamilyMemberModel.user_id == user_id)
            .order_by(FamilyMemberModel.created_at)
        )
        return [m.to_domain() for m in result.scalars().all()]

    async def list_by_keycloak_sub(self, keycloak_sub: str) -> list[FamilyMember]:
        """core/auth.py의 require_family가 토큰 sub → DB 행(들)을 해석할 때 사용."""
        result = await self._session.execute(
            select(FamilyMemberModel)
            .where(FamilyMemberModel.keycloak_sub == keycloak_sub)
            .order_by(FamilyMemberModel.created_at)
        )
        return [m.to_domain() for m in result.scalars().all()]

    async def create(
        self,
        user_id: uuid.UUID,
        role: FamilyRole,
        name: str,
        contact: str,
        keycloak_sub: str | None = None,
    ) -> FamilyMember:
        model = FamilyMemberModel(
            id=uuid.uuid4(),
            user_id=user_id,
            role=role.value,
            name=name,
            contact=contact,
            two_factor_enabled=False,
            keycloak_sub=keycloak_sub,
            created_at=datetime.now(UTC),
        )
        self._session.add(model)
        await self._session.flush()
        return model.to_domain()
