"""PhotoRequest 유스케이스 — WU3(가족이 요청) → WF3(당사자 알림) 흐름의 서버측."""

import uuid
from datetime import UTC, datetime

from core_service.core.errors import ApiError
from core_service.modules.photo_requests.domain.photo_request import PhotoRequest, PhotoRequestStatus
from core_service.modules.photo_requests.infrastructure.photo_request_repository import (
    PhotoRequestRepository,
)


class PhotoRequestService:
    def __init__(self, repo: PhotoRequestRepository):
        self._repo = repo

    async def create_request(
        self, user_id: uuid.UUID, requested_by: uuid.UUID | None, message: str | None
    ) -> PhotoRequest:
        if message is not None and len(message) > 300:
            raise ApiError("VALIDATION_ERROR", "message는 300자 이하여야 합니다.")
        return await self._repo.create(user_id=user_id, requested_by=requested_by, message=message)

    async def list_requests_for_user(self, user_id: uuid.UUID) -> list[PhotoRequest]:
        return await self._repo.list_by_user(user_id)

    async def dismiss_request(self, request_id: uuid.UUID) -> PhotoRequest:
        request = await self._get_or_404(request_id)
        try:
            request.ensure_dismissable()
        except ValueError as exc:
            raise ApiError("CONFLICT", str(exc)) from exc
        return await self._repo.update_status(request_id, PhotoRequestStatus.DISMISSED)

    async def fulfill_pending_for_user(self, user_id: uuid.UUID) -> list[PhotoRequest]:
        """schema.md §3.7 `fulfilled_at`: "사진 업로드로 충족된 시각" — photos 모듈의
        업로드 완료 콜백(POST /photos/{id}/complete)에서 호출한다(photos/api/v1/photos.py
        참조, deps.py를 통한 composition — structure.md §2 모듈 경계 원칙).

        어느 사진이 어느 요청에 대한 응답인지 연결하는 FK가 스키마에 없어(둘 다
        photos↔photo_requests 간 링크 컬럼이 없음), 이 사용자의 대기 중인 요청을
        전부 충족 처리한다 — "가족이 부탁했더니 사진을 올렸다"는 일반적 신호로
        해석한 것으로, 스키마가 명시적으로 정한 1:1 매핑은 아니다.
        """
        pending = await self._repo.list_pending_by_user(user_id)
        now = datetime.now(UTC)
        return [
            await self._repo.update_status(req.id, PhotoRequestStatus.FULFILLED, fulfilled_at=now)
            for req in pending
        ]

    async def _get_or_404(self, request_id: uuid.UUID) -> PhotoRequest:
        request = await self._repo.get_by_id(request_id)
        if request is None:
            raise ApiError("NOT_FOUND", f"사진 요청({request_id})을 찾을 수 없습니다.")
        return request
