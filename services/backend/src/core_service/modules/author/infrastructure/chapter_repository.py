"""chapters 테이블 SQLAlchemy 매핑 + Repository — schema.md §5 DDL과 1:1.

`body_text`는 PII 암호화 대상(schema.md §5, decisions.md #45) — 이 계층에서 투명하게
암복호화하므로 application/domain은 평문만 본다. 암호화 방식은 core/crypto.py 참조.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, SmallInteger, String, Text, select
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from core_service.core.crypto import PiiFieldEncryptor, get_pii_encryptor
from core_service.core.db import Base
from core_service.modules.author.domain.chapter import Chapter, ChapterPeriod, ChapterStatus


class ChapterModel(Base):
    __tablename__ = "chapters"

    id: Mapped[uuid.UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    chapter_no: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    period: Mapped[str] = mapped_column(
        SAEnum("childhood", "youth", "adulthood", "present", name="chapter_period", create_type=False),
        nullable=False,
    )
    body_text: Mapped[str] = mapped_column(Text, nullable=False)  # 저장 시 암호문(core/crypto.py)
    status: Mapped[str] = mapped_column(
        SAEnum("draft", "in_review", "rejected", "confirmed", name="chapter_status", create_type=False),
        nullable=False,
        default="draft",
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ChapterRepository:
    def __init__(self, session: AsyncSession, pii: PiiFieldEncryptor | None = None):
        self._session = session
        self._pii = pii or get_pii_encryptor()

    async def _to_domain(self, model: ChapterModel) -> Chapter:
        return Chapter(
            id=model.id,
            user_id=model.user_id,
            chapter_no=model.chapter_no,
            title=model.title,
            period=ChapterPeriod(model.period),
            body_text=await self._pii.decrypt(self._session, model.user_id, model.body_text),
            status=ChapterStatus(model.status),
            version=model.version,
            updated_at=model.updated_at,
        )

    async def get_by_id(self, chapter_id: uuid.UUID) -> Chapter | None:
        model = await self._session.get(ChapterModel, chapter_id)
        return await self._to_domain(model) if model else None

    async def list_by_user(self, user_id: uuid.UUID) -> list[Chapter]:
        result = await self._session.execute(
            select(ChapterModel).where(ChapterModel.user_id == user_id).order_by(ChapterModel.chapter_no)
        )
        return [await self._to_domain(m) for m in result.scalars().all()]

    async def list_updated_since(self, user_id: uuid.UUID, since: datetime | None = None) -> list[Chapter]:
        """GET /sync/download의 chapter_updates 소스 — sync-contract.md §5가 명시한
        "updated_at 기준 워터마크" 원칙 그대로. `since` 미지정 시 사용자의 전체 챕터
        (최초 동기화 스냅샷)를 돌려준다."""
        conditions = [ChapterModel.user_id == user_id]
        if since is not None:
            conditions.append(ChapterModel.updated_at > since)
        result = await self._session.execute(
            select(ChapterModel).where(*conditions).order_by(ChapterModel.updated_at)
        )
        return [await self._to_domain(m) for m in result.scalars().all()]

    async def get_by_user_and_no(self, user_id: uuid.UUID, chapter_no: int) -> Chapter | None:
        result = await self._session.execute(
            select(ChapterModel).where(ChapterModel.user_id == user_id, ChapterModel.chapter_no == chapter_no)
        )
        model = result.scalar_one_or_none()
        return await self._to_domain(model) if model else None

    async def upsert_draft(
        self,
        user_id: uuid.UUID,
        chapter_no: int,
        title: str,
        period: ChapterPeriod,
        body_text: str,
    ) -> Chapter:
        """workflow-diagrams.md §4 — 작가 엔진이 초안을 생성/갱신할 때 사용.

        기존 챕터(user_id, chapter_no)가 있으면 본문만 갱신(draft로 되돌리지 않음 —
        이미 감수 중/확정된 챕터를 파이프라인이 조용히 덮어쓰지 않도록 status는
        호출자가 명시적으로 넘기게 한다), 없으면 draft로 신규 생성한다.
        """
        body_cipher = await self._pii.encrypt(self._session, user_id, body_text)
        existing = await self._session.execute(
            select(ChapterModel).where(ChapterModel.user_id == user_id, ChapterModel.chapter_no == chapter_no)
        )
        model = existing.scalar_one_or_none()
        if model is not None:
            model.title = title
            model.period = period.value
            model.body_text = body_cipher
            model.version += 1
            model.updated_at = datetime.now(UTC)
        else:
            model = ChapterModel(
                id=uuid.uuid4(),
                user_id=user_id,
                chapter_no=chapter_no,
                title=title,
                period=period.value,
                body_text=body_cipher,
                status=ChapterStatus.DRAFT.value,
                version=1,
                updated_at=datetime.now(UTC),
            )
            self._session.add(model)
        await self._session.flush()
        return await self._to_domain(model)

    async def update_status(
        self, chapter_id: uuid.UUID, status: ChapterStatus, bump_version: bool = False
    ) -> Chapter:
        model = await self._session.get(ChapterModel, chapter_id)
        if model is None:
            raise LookupError(f"chapter {chapter_id} not found")
        model.status = status.value
        if bump_version:
            model.version += 1
        model.updated_at = datetime.now(UTC)
        await self._session.flush()
        return await self._to_domain(model)
