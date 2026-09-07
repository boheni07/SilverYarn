"""ChapterService 유닛 테스트 — 페이크 Repository로 DB 없이 Application 계층 검증.

핵심 검증 대상: workflow-diagrams.md M-5 정정 — chapter_revisions는 review_chapter()를
거칠 때만 생성되고, save_draft()(작가 엔진 초안 저장)는 절대 만들지 않는다.
"""

import uuid
from datetime import datetime

import pytest

from core_service.core.errors import ApiError
from core_service.modules.author.application.chapter_service import ChapterService
from core_service.modules.author.domain.chapter import (
    Chapter,
    ChapterPeriod,
    ChapterRevision,
    ChapterStatus,
    RevisionAction,
)


class FakeChapterRepository:
    def __init__(self) -> None:
        self.by_id: dict[uuid.UUID, Chapter] = {}

    async def get_by_id(self, chapter_id: uuid.UUID) -> Chapter | None:
        return self.by_id.get(chapter_id)

    async def list_by_user(self, user_id: uuid.UUID) -> list[Chapter]:
        return sorted((c for c in self.by_id.values() if c.user_id == user_id), key=lambda c: c.chapter_no)

    async def upsert_draft(
        self,
        user_id: uuid.UUID,
        chapter_no: int,
        title: str,
        period: ChapterPeriod,
        body_text: str,
    ) -> Chapter:
        existing = next(
            (c for c in self.by_id.values() if c.user_id == user_id and c.chapter_no == chapter_no),
            None,
        )
        if existing:
            existing.title = title
            existing.period = period
            existing.body_text = body_text
            existing.version += 1
            existing.updated_at = datetime.now()
            return existing
        chapter = Chapter(
            id=uuid.uuid4(),
            user_id=user_id,
            chapter_no=chapter_no,
            title=title,
            period=period,
            body_text=body_text,
            status=ChapterStatus.DRAFT,
            version=1,
            updated_at=datetime.now(),
        )
        self.by_id[chapter.id] = chapter
        return chapter

    async def update_status(
        self, chapter_id: uuid.UUID, status: ChapterStatus, bump_version: bool = False
    ) -> Chapter:
        chapter = self.by_id[chapter_id]
        chapter.status = status
        if bump_version:
            chapter.version += 1
        chapter.updated_at = datetime.now()
        return chapter


class FakeChapterRevisionRepository:
    def __init__(self) -> None:
        self.revisions: list[ChapterRevision] = []

    async def list_by_chapter(self, chapter_id: uuid.UUID) -> list[ChapterRevision]:
        return [r for r in self.revisions if r.chapter_id == chapter_id]

    async def create(
        self,
        chapter_id: uuid.UUID,
        version: int,
        body_text_snapshot: str,
        reviewer_id: uuid.UUID | None,
        review_comment: str | None,
        action: RevisionAction,
    ) -> ChapterRevision:
        revision = ChapterRevision(
            id=uuid.uuid4(),
            chapter_id=chapter_id,
            version=version,
            body_text_snapshot=body_text_snapshot,
            reviewer_id=reviewer_id,
            review_comment=review_comment,
            action=action,
            created_at=datetime.now(),
        )
        self.revisions.append(revision)
        return revision


@pytest.fixture
def chapters() -> FakeChapterRepository:
    return FakeChapterRepository()


@pytest.fixture
def revisions() -> FakeChapterRevisionRepository:
    return FakeChapterRevisionRepository()


@pytest.fixture
def service(chapters: FakeChapterRepository, revisions: FakeChapterRevisionRepository) -> ChapterService:
    return ChapterService(chapters, revisions)  # type: ignore[arg-type]


async def test_save_draft_creates_new_chapter_without_revision(
    service: ChapterService, revisions: FakeChapterRevisionRepository
) -> None:
    user_id = uuid.uuid4()
    chapter = await service.save_draft(
        user_id=user_id,
        chapter_no=2,
        title="인천 공장 시절",
        period=ChapterPeriod.YOUTH,
        body_text="1978년 인천의 작은 기계공장에서...",
    )
    assert chapter.status == ChapterStatus.DRAFT
    assert chapter.version == 1
    # M-5 핵심: 초안 저장만으로는 chapter_revisions가 절대 생기지 않는다
    assert await revisions.list_by_chapter(chapter.id) == []


async def test_save_draft_upserts_and_bumps_version(service: ChapterService) -> None:
    user_id = uuid.uuid4()
    first = await service.save_draft(
        user_id=user_id, chapter_no=1, title="A", period=ChapterPeriod.CHILDHOOD, body_text="초안1"
    )
    second = await service.save_draft(
        user_id=user_id, chapter_no=1, title="A 개정", period=ChapterPeriod.CHILDHOOD, body_text="초안2"
    )
    assert second.id == first.id
    assert second.version == 2
    assert second.body_text == "초안2"


async def test_review_chapter_approved_creates_revision_and_confirms(
    service: ChapterService, revisions: FakeChapterRevisionRepository
) -> None:
    user_id = uuid.uuid4()
    chapter = await service.save_draft(
        user_id=user_id, chapter_no=1, title="A", period=ChapterPeriod.CHILDHOOD, body_text="본문"
    )
    reviewer_id = uuid.uuid4()
    result = await service.review_chapter(
        chapter_id=chapter.id,
        reviewer_id=reviewer_id,
        action=RevisionAction.APPROVED,
        comment="좋습니다",
    )
    assert result.status == ChapterStatus.CONFIRMED
    saved = await revisions.list_by_chapter(chapter.id)
    assert len(saved) == 1
    assert saved[0].action == RevisionAction.APPROVED
    assert saved[0].body_text_snapshot == "본문"
    assert saved[0].reviewer_id == reviewer_id


async def test_review_chapter_rejected_sets_rejected_status(service: ChapterService) -> None:
    user_id = uuid.uuid4()
    chapter = await service.save_draft(
        user_id=user_id, chapter_no=1, title="A", period=ChapterPeriod.CHILDHOOD, body_text="본문"
    )
    result = await service.review_chapter(
        chapter_id=chapter.id, reviewer_id=None, action=RevisionAction.REJECTED, comment="다시 써주세요"
    )
    assert result.status == ChapterStatus.REJECTED


async def test_review_already_confirmed_chapter_raises_conflict(service: ChapterService) -> None:
    user_id = uuid.uuid4()
    chapter = await service.save_draft(
        user_id=user_id, chapter_no=1, title="A", period=ChapterPeriod.CHILDHOOD, body_text="본문"
    )
    await service.review_chapter(
        chapter_id=chapter.id, reviewer_id=None, action=RevisionAction.APPROVED, comment=None
    )
    with pytest.raises(ApiError) as exc_info:
        await service.review_chapter(
            chapter_id=chapter.id, reviewer_id=None, action=RevisionAction.APPROVED, comment=None
        )
    assert exc_info.value.code == "CONFLICT"


async def test_get_chapter_not_found(service: ChapterService) -> None:
    with pytest.raises(ApiError) as exc_info:
        await service.get_chapter(uuid.uuid4())
    assert exc_info.value.code == "NOT_FOUND"


async def test_save_draft_rejects_empty_body(service: ChapterService) -> None:
    with pytest.raises(ApiError) as exc_info:
        await service.save_draft(
            user_id=uuid.uuid4(),
            chapter_no=1,
            title="A",
            period=ChapterPeriod.CHILDHOOD,
            body_text="",
        )
    assert exc_info.value.code == "VALIDATION_ERROR"
