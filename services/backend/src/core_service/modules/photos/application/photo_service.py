"""Photo 유스케이스 — sync-contract.md §4 Presigned URL 업로드 흐름 + 목록 조회.

⚠️ 오케스트레이션 책임 경계: 이 서비스는 `photos` 행 생성/상태 전이와 MinIO
Presigned URL 발급만 담당한다. AI 자동 인라인 삽입 제안(placement_status=proposed
→ 챕터 본문 편입)은 author 모듈의 몫이라 여기서 다루지 않는다.
"""

import logging
import uuid
from datetime import UTC, datetime, timedelta

from core_service.core.clients.storage_client import StorageClient
from core_service.core.errors import ApiError
from core_service.modules.photos.domain.photo import Photo, PhotoUploadStatus, UploaderType
from core_service.modules.photos.infrastructure.photo_repository import PhotoRepository

logger = logging.getLogger(__name__)

# sync-contract.md §4 "24시간 지나도 pending_upload면 정리(orphan cleanup)"
_ORPHAN_CLEANUP_THRESHOLD = timedelta(hours=24)

# decisions.md #10 — 클라이언트 리사이즈(장변 1600px)·JPEG 80% 압축을 온디바이스에서
# 먼저 하므로, 서버가 실제로 받는 포맷은 사실상 JPEG 하나다. PNG/WEBP는 웹 콘솔
# 업로드(가족이 스캔한 옛날 사진 등, 압축 정책 미적용) 대비 폭넓게 허용해 둔다.
_ALLOWED_CONTENT_TYPES = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}

_UPLOAD_URL_TTL = timedelta(minutes=15)  # sync-contract.md §4 1단계 스펙


class PhotoService:
    def __init__(self, repo: PhotoRepository, storage: StorageClient):
        self._repo = repo
        self._storage = storage

    async def request_upload_url(
        self,
        user_id: uuid.UUID,
        uploader_type: UploaderType,
        content_type: str,
        file_size: int,
    ) -> tuple[Photo, str, datetime]:
        """POST /photos/upload-url — sync-contract.md §4 1단계.
        (Photo, upload_url, expires_at) 튜플 반환."""
        if content_type not in _ALLOWED_CONTENT_TYPES:
            allowed = ", ".join(_ALLOWED_CONTENT_TYPES)
            raise ApiError(
                "VALIDATION_ERROR", f"지원하지 않는 content_type입니다: {content_type} (허용: {allowed})"
            )
        if file_size <= 0:
            raise ApiError("VALIDATION_ERROR", "file_size는 0보다 커야 합니다.")

        await self._storage.ensure_bucket()

        photo_id = uuid.uuid4()
        extension = _ALLOWED_CONTENT_TYPES[content_type]
        object_name = f"{user_id}/{photo_id}.{extension}"

        photo = await self._repo.create_pending(
            photo_id=photo_id,
            user_id=user_id,
            uploader_type=uploader_type,
            storage_ref=object_name,
            mime_type=content_type,
            file_size_kb=file_size // 1024 or 1,
        )
        upload_url = self._storage.presigned_put_url(object_name, expires=_UPLOAD_URL_TTL)
        expires_at = datetime.now(UTC) + _UPLOAD_URL_TTL
        return photo, upload_url, expires_at

    async def complete_upload(self, photo_id: uuid.UUID) -> Photo:
        """POST /photos/{id}/complete — sync-contract.md §4 3단계.
        이미 uploaded인 photo를 다시 완료 처리해도 멱등하게 성공한다(클라이언트
        재시도로 인한 중복 콜백을 실패로 만들지 않기 위함)."""
        photo = await self._repo.get_by_id(photo_id)
        if photo is None:
            raise ApiError("NOT_FOUND", f"사진({photo_id})을 찾을 수 없습니다.")
        if photo.status == PhotoUploadStatus.UPLOADED:
            return photo
        return await self._repo.mark_uploaded(photo_id)

    async def list_photos_for_user(self, user_id: uuid.UUID) -> list[Photo]:
        """GET /users/{userId}/photos — design.md §4.2."""
        return await self._repo.list_by_user(user_id)

    async def cleanup_orphan_pending_uploads(self, older_than: timedelta = _ORPHAN_CLEANUP_THRESHOLD) -> int:
        """sync-contract.md §4 orphan cleanup — worker.py의 arq cron job이 주기적으로
        호출한다(API 라우터에서 직접 부르지 않음). 3단계 확인 콜백이 끝내 안 온
        pending_upload 행을 지운다 — MinIO 삭제는 best-effort(대부분은 presigned
        URL을 아예 안 써서 객체 자체가 없는 게 정상 케이스, remove_object 주석 참조).
        DB 삭제가 실패하면 그 사진은 건너뛰고 다음 배치 실행에 다시 시도한다."""
        threshold = datetime.now(UTC) - older_than
        orphans = await self._repo.list_pending_upload_older_than(threshold)

        cleaned = 0
        for photo in orphans:
            try:
                await self._storage.remove_object(photo.storage_ref)
                await self._repo.delete(photo.id)
            except Exception:
                logger.exception(
                    "photos orphan cleanup 실패 — photo_id=%s, storage_ref=%s", photo.id, photo.storage_ref
                )
                continue
            cleaned += 1
        return cleaned
