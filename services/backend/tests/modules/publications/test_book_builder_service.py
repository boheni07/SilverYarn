"""BookBuilderService 유닛 테스트 — 페이크 Repository/ChapterService/StorageClient로
실제 PDF/ePub 바이트가 생성되고 올바른 순서로 상태 전이·업로드되는지 검증한다.

실제 reportlab/EbookLib 라이브러리는 그대로 호출한다(순수 로컬 렌더링이라 페이크할
필요가 없고, 오히려 실제 산출물 바이트를 검증하는 게 더 의미 있다) — 외부 I/O만
페이크(MinIO 업로드)로 대체한다.
"""

import uuid
from datetime import UTC, datetime

from core_service.modules.author.domain.chapter import Chapter, ChapterPeriod, ChapterStatus
from core_service.modules.publications.application.book_builder_service import BookBuilderService
from core_service.modules.publications.domain.publication import (
    Publication,
    PublicationFormat,
    PublicationStatus,
)


def _chapter(user_id: uuid.UUID, chapter_no: int) -> Chapter:
    return Chapter(
        id=uuid.uuid4(),
        user_id=user_id,
        chapter_no=chapter_no,
        title=f"1978년 인천 공장 이야기 {chapter_no}",
        period=ChapterPeriod.YOUTH,
        body_text="첫 문단입니다.\n\n둘째 문단입니다. <특수문자>도 & 포함합니다.",
        status=ChapterStatus.CONFIRMED,
        version=1,
        updated_at=datetime.now(UTC),
    )


class FakeChapterService:
    def __init__(self, chapters: list[Chapter]) -> None:
        self._chapters = chapters

    async def list_chapters_for_user(self, user_id: uuid.UUID) -> list[Chapter]:
        return [c for c in self._chapters if c.user_id == user_id]


class FakePublicationRepository:
    def __init__(self, publication: Publication) -> None:
        self._publication = publication
        self.calls: list[str] = []

    async def get_by_id(self, publication_id: uuid.UUID) -> Publication | None:
        return self._publication if publication_id == self._publication.id else None

    async def mark_processing(self, publication_id: uuid.UUID) -> None:
        self.calls.append("mark_processing")
        self._publication = Publication(
            **{**self._publication.__dict__, "status": PublicationStatus.PROCESSING}
        )

    async def mark_ready(self, publication_id: uuid.UUID, storage_ref: str) -> None:
        self.calls.append(f"mark_ready:{storage_ref}")
        self._publication = Publication(
            **{
                **self._publication.__dict__,
                "status": PublicationStatus.READY,
                "storage_ref": storage_ref,
            }
        )


class FakeStorageClient:
    publications_bucket = "silveryarn-publications-test"

    def __init__(self) -> None:
        self.uploaded: list[tuple[str, bytes, str, str]] = []
        self.ensured_buckets: list[str] = []

    async def ensure_bucket(self, bucket: str | None = None) -> None:
        self.ensured_buckets.append(bucket or "")

    async def put_object(
        self, object_name: str, data: bytes, content_type: str, bucket: str | None = None
    ) -> None:
        self.uploaded.append((object_name, data, content_type, bucket or ""))


async def test_build_pdf_generates_bytes_and_transitions_status() -> None:
    user_id = uuid.uuid4()
    publication = Publication(
        id=uuid.uuid4(),
        user_id=user_id,
        format=PublicationFormat.HARDCOVER_PDF,
        status=PublicationStatus.REQUESTED,
        storage_ref=None,
        requested_at=datetime.now(UTC),
        completed_at=None,
    )
    repo = FakePublicationRepository(publication)
    storage = FakeStorageClient()
    service = BookBuilderService(
        repo,
        FakeChapterService([_chapter(user_id, 1), _chapter(user_id, 2)]),
        storage,  # type: ignore[arg-type]
    )

    await service.build(publication.id)

    assert repo.calls[0] == "mark_processing"
    assert repo.calls[1].startswith("mark_ready:")
    assert len(storage.uploaded) == 1
    object_name, data, content_type, bucket = storage.uploaded[0]
    assert object_name == f"{user_id}/{publication.id}.pdf"
    assert content_type == "application/pdf"
    assert bucket == storage.publications_bucket
    assert data[:5] == b"%PDF-"  # 실제 PDF 매직바이트 — reportlab이 진짜 PDF를 만들었는지 확인


async def test_build_epub_generates_valid_zip_container() -> None:
    user_id = uuid.uuid4()
    publication = Publication(
        id=uuid.uuid4(),
        user_id=user_id,
        format=PublicationFormat.EPUB,
        status=PublicationStatus.REQUESTED,
        storage_ref=None,
        requested_at=datetime.now(UTC),
        completed_at=None,
    )
    repo = FakePublicationRepository(publication)
    storage = FakeStorageClient()
    service = BookBuilderService(
        repo,
        FakeChapterService([_chapter(user_id, 1)]),
        storage,  # type: ignore[arg-type]
    )

    await service.build(publication.id)

    object_name, data, content_type, _ = storage.uploaded[0]
    assert object_name == f"{user_id}/{publication.id}.epub"
    assert content_type == "application/epub+zip"
    assert data[:4] == b"PK\x03\x04"  # ePub은 ZIP 컨테이너 — 매직바이트로 실제 생성 확인


async def test_build_raises_when_publication_not_found() -> None:
    storage = FakeStorageClient()

    class _EmptyRepo(FakePublicationRepository):
        async def get_by_id(self, publication_id: uuid.UUID) -> Publication | None:
            return None

    dummy = Publication(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        format=PublicationFormat.EPUB,
        status=PublicationStatus.REQUESTED,
        storage_ref=None,
        requested_at=datetime.now(UTC),
        completed_at=None,
    )
    service = BookBuilderService(_EmptyRepo(dummy), FakeChapterService([]), storage)  # type: ignore[arg-type]
    try:
        await service.build(uuid.uuid4())
    except LookupError:
        pass
    else:
        raise AssertionError("LookupError를 기대했지만 발생하지 않음")
