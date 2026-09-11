"""users 테이블 SQLAlchemy 매핑 + Repository — schema.md §5 DDL과 1:1.

`birth_date`는 PII 암호화 대상(decisions.md #45 2차) — DB 컬럼은 VARCHAR로 암호문을
보관하고, 이 계층에서 사용자 자신의 DEK로 투명하게 암복호화한다(core/crypto.py).
`name`은 평문 유지(부분검색 UX·낮은 민감도, decisions.md #45 2차).
"""

import uuid
from datetime import UTC, date, datetime

from sqlalchemy import ARRAY, DateTime, Integer, String, func, select
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from core_service.core.crypto import PiiFieldEncryptor, get_pii_encryptor
from core_service.core.db import Base
from core_service.modules.users.domain.user import PersonaSnapshot, User


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # 평문
    birth_date: Mapped[str | None] = mapped_column(String(200), nullable=True)  # 저장 시 암호문
    primary_device_id: Mapped[uuid.UUID | None] = mapped_column(PgUUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    # §2.11 4단계 "단기 압축 기억" (마이그레이션 0008) — compaction_summary(챕터별)와
    # 동일하게 평문(일관성 우선, 모듈 docstring 참조).
    persona_summary: Mapped[str | None] = mapped_column(String(500), nullable=True)
    persona_keywords: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    persona_source_chapter_count: Mapped[int | None] = mapped_column(Integer, nullable=True)


class UserRepository:
    """Domain이 필요로 하는 영속화 인터페이스의 구현체 (structure.md §6 의존성 역전)."""

    def __init__(self, session: AsyncSession, pii: PiiFieldEncryptor | None = None):
        self._session = session
        self._pii = pii or get_pii_encryptor()

    async def _to_domain(self, model: UserModel) -> User:
        birth_raw = await self._pii.decrypt_opt(self._session, model.id, model.birth_date)
        persona: PersonaSnapshot | None = None
        if model.persona_summary is not None and model.persona_source_chapter_count is not None:
            persona = PersonaSnapshot(
                summary=model.persona_summary,
                keywords=list(model.persona_keywords or []),
                source_chapter_count=model.persona_source_chapter_count,
            )
        return User(
            id=model.id,
            name=model.name,
            birth_date=date.fromisoformat(birth_raw) if birth_raw else None,
            primary_device_id=model.primary_device_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            persona_snapshot=persona,
        )

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        model = await self._session.get(UserModel, user_id)
        return await self._to_domain(model) if model else None

    async def list_all(self, offset: int, limit: int, name: str | None = None) -> tuple[list[User], int]:
        """apps/admin "전체 사용자 목록" — design.md §4.1 표준 페이지네이션 봉투.
        정렬은 created_at DESC(최근 가입자 먼저). `name`은 평문이라 ILIKE 부분일치가 최종 구현
        (decisions.md #45 2차 — name은 암호화하지 않음). 규모가 커지면 idx_users_created_at 검토.
        """
        conditions = [UserModel.name.ilike(f"%{name}%")] if name else []

        count_result = await self._session.execute(
            select(func.count()).select_from(UserModel).where(*conditions)
        )
        total = count_result.scalar_one()

        stmt = (
            select(UserModel)
            .where(*conditions)
            .order_by(UserModel.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        users = [await self._to_domain(model) for model in result.scalars()]
        return users, total

    async def create(self, name: str, birth_date: date | None) -> User:
        model = UserModel(
            id=uuid.uuid4(),
            name=name,
            birth_date=None,
            primary_device_id=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        self._session.add(model)
        await self._session.flush()  # id 확정 후 DEK 조회 가능
        if birth_date is not None:
            model.birth_date = await self._pii.encrypt(self._session, model.id, birth_date.isoformat())
            await self._session.flush()
        return await self._to_domain(model)

    async def set_primary_device(self, user_id: uuid.UUID, device_id: uuid.UUID) -> None:
        model = await self._session.get(UserModel, user_id)
        if model is None:
            raise LookupError(f"user {user_id} not found")
        model.primary_device_id = device_id
        model.updated_at = datetime.now(UTC)
        await self._session.flush()

    async def set_persona_snapshot(
        self, user_id: uuid.UUID, *, summary: str, keywords: list[str], source_chapter_count: int
    ) -> None:
        """§2.11 4단계 "단기 압축 기억" 저장. `compaction_summary`(chapters, 0007)와
        마찬가지로 `updated_at`은 건드리지 않는다 — 요약 갱신만으로 다른 신선도
        기준(예: 프로필 변경 감지)이 흔들리면 안 된다."""
        model = await self._session.get(UserModel, user_id)
        if model is None:
            raise LookupError(f"user {user_id} not found")
        model.persona_summary = summary[:500]
        model.persona_keywords = keywords
        model.persona_source_chapter_count = source_chapter_count
        await self._session.flush()
