"""PhotoService 유닛 테스트 — 페이크 Repository/StorageClient로 DB·MinIO 없이
Application 계층 검증.

핵심 검증 대상: sync-contract.md §4 Presigned URL 3단계 흐름
(upload-url 발급 → status=pending_upload 생성 → complete 콜백 → status=uploaded)이
정확히 구현됐는지, 그리고 잘못된 content_type/file_size를 걸러내는지.
"""

import uuid
from datetime import UTC, datetime, timedelta
from datetime import timedelta as _timedelta

import pytest

from core_service.core.errors import ApiError
from core_service.modules.photos.application.photo_service import PhotoService
from core_service.modules.photos.domain.photo import (
    Photo,
    PhotoUploadStatus,
    PlacementStatus,
    QualityFlag,
    RecallStatus,
    UploaderType,
)


class FakePhotoRepository:
    def __init__(self) -> None:
        self._store: dict[uuid.UUID, Photo] = {}

    async def get_by_id(self, photo_id: uuid.UUID) -> Photo | None:
        return self._store.get(photo_id)

    async def list_by_user(self, user_id: uuid.UUID) -> list[Photo]:
        photos = [p for p in self._store.values() if p.user_id == user_id]
        return sorted(photos, key=lambda p: p.uploaded_at, reverse=True)

    async def create_pending(
        self,
        photo_id: uuid.UUID,
        user_id: uuid.UUID,
        uploader_type: UploaderType,
        storage_ref: str,
        mime_type: str | None,
        file_size_kb: int | None,
    ) -> Photo:
        photo = Photo(
            id=photo_id,
            user_id=user_id,
            uploader_type=uploader_type,
            status=PhotoUploadStatus.PENDING_UPLOAD,
            storage_ref=storage_ref,
            caption=None,
            year_tag=None,
            recall_status=RecallStatus.PENDING,
            placement_status=PlacementStatus.PROPOSED,
            inline_position=None,
            linked_chunk_id=None,
            linked_chapter_id=None,
            quality_flag=QualityFlag.UNREVIEWED,
            width=None,
            height=None,
            file_size_kb=file_size_kb,
            mime_type=mime_type,
            uploaded_at=datetime.now(UTC),
        )
        self._store[photo.id] = photo
        return photo

    async def mark_uploaded(self, photo_id: uuid.UUID) -> Photo:
        photo = self._store[photo_id]
        photo.status = PhotoUploadStatus.UPLOADED
        return photo

    async def list_pending_upload_older_than(self, threshold: datetime) -> list[Photo]:
        return [
            p
            for p in self._store.values()
            if p.status == PhotoUploadStatus.PENDING_UPLOAD and p.uploaded_at < threshold
        ]

    async def delete(self, photo_id: uuid.UUID) -> None:
        self._store.pop(photo_id, None)


class FakeStorageClient:
    def __init__(self) -> None:
        self.ensure_bucket_called = False
        self.removed_objects: list[str] = []

    async def ensure_bucket(self) -> None:
        self.ensure_bucket_called = True

    def presigned_put_url(self, object_name: str, expires: _timedelta = timedelta(minutes=15)) -> str:
        return f"https://minio.internal/silveryarn-photos/{object_name}?signed=1"

    async def remove_object(self, object_name: str) -> None:
        self.removed_objects.append(object_name)


@pytest.fixture
def repo() -> FakePhotoRepository:
    return FakePhotoRepository()


@pytest.fixture
def storage() -> FakeStorageClient:
    return FakeStorageClient()


@pytest.fixture
def service(repo: FakePhotoRepository, storage: FakeStorageClient) -> PhotoService:
    return PhotoService(repo, storage)  # type: ignore[arg-type]


class TestRequestUploadUrl:
    async def test_pending_상태로_photo_행_생성(self, service: PhotoService) -> None:
        user_id = uuid.uuid4()
        photo, upload_url, expires_at = await service.request_upload_url(
            user_id=user_id, uploader_type=UploaderType.SELF, content_type="image/jpeg", file_size=482913
        )

        assert photo.status == PhotoUploadStatus.PENDING_UPLOAD
        assert photo.user_id == user_id
        assert photo.uploader_type == UploaderType.SELF
        assert "signed=1" in upload_url
        assert photo.storage_ref in upload_url

    async def test_버킷을_먼저_보장한다(self, service: PhotoService, storage: FakeStorageClient) -> None:
        await service.request_upload_url(
            user_id=uuid.uuid4(), uploader_type=UploaderType.FAMILY, content_type="image/jpeg", file_size=1000
        )
        assert storage.ensure_bucket_called

    async def test_지원하지_않는_content_type은_VALIDATION_ERROR(self, service: PhotoService) -> None:
        with pytest.raises(ApiError) as exc_info:
            await service.request_upload_url(
                user_id=uuid.uuid4(),
                uploader_type=UploaderType.SELF,
                content_type="application/pdf",
                file_size=1000,
            )
        assert exc_info.value.code == "VALIDATION_ERROR"

    async def test_file_size가_0_이하면_VALIDATION_ERROR(self, service: PhotoService) -> None:
        with pytest.raises(ApiError) as exc_info:
            await service.request_upload_url(
                user_id=uuid.uuid4(), uploader_type=UploaderType.SELF, content_type="image/jpeg", file_size=0
            )
        assert exc_info.value.code == "VALIDATION_ERROR"


class TestCompleteUpload:
    async def test_pending을_uploaded로_전이(self, service: PhotoService) -> None:
        photo, _, _ = await service.request_upload_url(
            user_id=uuid.uuid4(), uploader_type=UploaderType.SELF, content_type="image/jpeg", file_size=1000
        )

        completed = await service.complete_upload(photo.id)

        assert completed.status == PhotoUploadStatus.UPLOADED

    async def test_이미_uploaded면_멱등하게_성공(self, service: PhotoService) -> None:
        photo, _, _ = await service.request_upload_url(
            user_id=uuid.uuid4(), uploader_type=UploaderType.SELF, content_type="image/jpeg", file_size=1000
        )
        await service.complete_upload(photo.id)

        result = await service.complete_upload(photo.id)

        assert result.status == PhotoUploadStatus.UPLOADED

    async def test_존재하지_않는_사진은_NOT_FOUND(self, service: PhotoService) -> None:
        with pytest.raises(ApiError) as exc_info:
            await service.complete_upload(uuid.uuid4())
        assert exc_info.value.code == "NOT_FOUND"


class TestListPhotosForUser:
    async def test_다른_사용자_사진은_제외(self, service: PhotoService) -> None:
        user_a = uuid.uuid4()
        user_b = uuid.uuid4()
        await service.request_upload_url(
            user_id=user_a, uploader_type=UploaderType.SELF, content_type="image/jpeg", file_size=1000
        )
        await service.request_upload_url(
            user_id=user_b, uploader_type=UploaderType.SELF, content_type="image/jpeg", file_size=1000
        )

        result = await service.list_photos_for_user(user_a)

        assert len(result) == 1
        assert result[0].user_id == user_a

    async def test_사진_없으면_빈_목록(self, service: PhotoService) -> None:
        result = await service.list_photos_for_user(uuid.uuid4())
        assert result == []


class TestCleanupOrphanPendingUploads:
    """sync-contract.md §4 orphan cleanup — worker.py의 arq cron job이 호출."""

    async def test_임계값보다_오래된_pending만_정리(
        self, service: PhotoService, repo: FakePhotoRepository, storage: FakeStorageClient
    ) -> None:
        old_photo, _, _ = await service.request_upload_url(
            user_id=uuid.uuid4(), uploader_type=UploaderType.SELF, content_type="image/jpeg", file_size=1000
        )
        repo._store[old_photo.id].uploaded_at = datetime.now(UTC) - timedelta(hours=25)

        recent_photo, _, _ = await service.request_upload_url(
            user_id=uuid.uuid4(), uploader_type=UploaderType.SELF, content_type="image/jpeg", file_size=1000
        )

        cleaned = await service.cleanup_orphan_pending_uploads()

        assert cleaned == 1
        assert await repo.get_by_id(old_photo.id) is None
        assert await repo.get_by_id(recent_photo.id) is not None
        assert storage.removed_objects == [old_photo.storage_ref]

    async def test_이미_uploaded면_정리_대상_아님(
        self, service: PhotoService, repo: FakePhotoRepository
    ) -> None:
        photo, _, _ = await service.request_upload_url(
            user_id=uuid.uuid4(), uploader_type=UploaderType.SELF, content_type="image/jpeg", file_size=1000
        )
        await service.complete_upload(photo.id)
        repo._store[photo.id].uploaded_at = datetime.now(UTC) - timedelta(hours=25)

        cleaned = await service.cleanup_orphan_pending_uploads()

        assert cleaned == 0
        assert await repo.get_by_id(photo.id) is not None

    async def test_정리_대상_없으면_0_반환(self, service: PhotoService) -> None:
        assert await service.cleanup_orphan_pending_uploads() == 0
