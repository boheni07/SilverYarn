"""PublicationService 유닛 테스트 — 페이크 Repository/ChapterService/ArqRedis로 DB 없이
Application 계층 검증.

design.md §2.6 — "전체 챕터 confirmed 상태 도달" 전제조건 검증이 핵심 검증 대상이다.
"""

import uuid
from datetime import UTC, datetime

import pytest

from core_service.core.errors import ApiError
from core_service.modules.author.domain.chapter import Chapter, ChapterPeriod, ChapterStatus
from core_service.modules.publications.application.publication_service import PublicationService
from core_service.modules.publications.domain.publication import (
    Publication,
    PublicationFormat,
    PublicationStatus,
)


def _chapter(user_id: uuid.UUID, chapter_no: int, status: ChapterStatus) -> Chapter:
    return Chapter(
        id=uuid.uuid4(),
        user_id=user_id,
        chapter_no=chapter_no,
        title=f"챕터 {chapter_no}",
        period=ChapterPeriod.YOUTH,
        body_text="본문",
        status=status,
        version=1,
        updated_at=datetime.now(UTC),
    )


class FakeChapterService:
    def __init__(self, chapters: list[Chapter]) -> None:
        self._chapters = chapters

    async def list_chapters_for_user(self, user_id: uuid.UUID) -> list[Chapter]:
        return [c for c in self._chapters if c.user_id == user_id]


class FakePublicationRepository:
    def __init__(self) -> None:
        self._store: dict[uuid.UUID, Publication] = {}

    async def create(self, user_id: uuid.UUID, fmt: PublicationFormat) -> Publication:
        publication = Publication(
            id=uuid.uuid4(),
            user_id=user_id,
            format=fmt,
            status=PublicationStatus.REQUESTED,
            storage_ref=None,
            requested_at=datetime.now(UTC),
            completed_at=None,
        )
        self._store[publication.id] = publication
        return publication

    async def get_by_id(self, publication_id: uuid.UUID) -> Publication | None:
        return self._store.get(publication_id)

    async def list_by_user(self, user_id: uuid.UUID) -> list[Publication]:
        return [p for p in self._store.values() if p.user_id == user_id]


class FakeArqPool:
    def __init__(self) -> None:
        self.enqueued: list[dict] = []

    async def enqueue_job(self, function: str, **kwargs) -> None:
        self.enqueued.append({"function": function, **kwargs})
        return None


def _service(chapters: list[Chapter]) -> tuple[PublicationService, FakePublicationRepository, FakeArqPool]:
    repo = FakePublicationRepository()
    pool = FakeArqPool()
    service = PublicationService(repo, FakeChapterService(chapters), pool)  # type: ignore[arg-type]
    return service, repo, pool


async def test_request_publication_rejects_when_no_chapters() -> None:
    service, _, _ = _service([])
    with pytest.raises(ApiError) as exc_info:
        await service.request_publication(uuid.uuid4(), PublicationFormat.EPUB)
    assert exc_info.value.code == "VALIDATION_ERROR"


async def test_request_publication_rejects_when_chapter_not_confirmed() -> None:
    user_id = uuid.uuid4()
    chapters = [
        _chapter(user_id, 1, ChapterStatus.CONFIRMED),
        _chapter(user_id, 2, ChapterStatus.IN_REVIEW),
    ]
    service, _, _ = _service(chapters)
    with pytest.raises(ApiError, match="확정되지 않은 챕터"):
        await service.request_publication(user_id, PublicationFormat.EPUB)


async def test_request_publication_succeeds_when_all_confirmed() -> None:
    user_id = uuid.uuid4()
    chapters = [
        _chapter(user_id, 1, ChapterStatus.CONFIRMED),
        _chapter(user_id, 2, ChapterStatus.CONFIRMED),
    ]
    service, repo, pool = _service(chapters)

    publication = await service.request_publication(user_id, PublicationFormat.HARDCOVER_PDF)

    assert publication.status == PublicationStatus.REQUESTED
    assert publication.format == PublicationFormat.HARDCOVER_PDF
    assert await repo.get_by_id(publication.id) is not None
    assert pool.enqueued == [{"function": "process_publication", "publication_id": str(publication.id)}]


async def test_request_publication_ignores_other_users_chapters() -> None:
    """다른 사용자의 미확정 챕터가 있어도 요청자 본인의 챕터만 검증 대상이다."""
    user_id = uuid.uuid4()
    other_id = uuid.uuid4()
    chapters = [
        _chapter(user_id, 1, ChapterStatus.CONFIRMED),
        _chapter(other_id, 1, ChapterStatus.DRAFT),
    ]
    service, _, _ = _service(chapters)
    publication = await service.request_publication(user_id, PublicationFormat.EPUB)
    assert publication.user_id == user_id


async def test_get_publication_not_found_raises_api_error() -> None:
    service, _, _ = _service([])
    with pytest.raises(ApiError) as exc_info:
        await service.get_publication(uuid.uuid4())
    assert exc_info.value.code == "NOT_FOUND"


async def test_list_publications_for_user_filters_by_user() -> None:
    user_id = uuid.uuid4()
    other_id = uuid.uuid4()
    chapters = [_chapter(user_id, 1, ChapterStatus.CONFIRMED), _chapter(other_id, 1, ChapterStatus.CONFIRMED)]
    service, _, _ = _service(chapters)
    await service.request_publication(user_id, PublicationFormat.EPUB)
    await service.request_publication(other_id, PublicationFormat.EPUB)

    results = await service.list_publications_for_user(user_id)
    assert len(results) == 1
    assert results[0].user_id == user_id
