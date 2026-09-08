"""PhotoRequestService 유닛 테스트 — 페이크 Repository로 DB 없이 Application 계층 검증.

핵심 검증 대상: WU3(가족이 요청) → WF3(당사자 확인) 루프의 세 갈래(fulfilled/
dismissed/pending 그대로 유지)가 정확히 구현됐는지 — 특히 fulfill_pending_for_user()가
photos 모듈 업로드 완료 콜백에서 호출되는 자동 충족 경로다.
"""

import uuid
from datetime import UTC, datetime

import pytest

from core_service.core.errors import ApiError
from core_service.modules.photo_requests.application.photo_request_service import PhotoRequestService
from core_service.modules.photo_requests.domain.photo_request import PhotoRequest, PhotoRequestStatus


class FakePhotoRequestRepository:
    def __init__(self) -> None:
        self._store: dict[uuid.UUID, PhotoRequest] = {}

    async def get_by_id(self, request_id: uuid.UUID) -> PhotoRequest | None:
        return self._store.get(request_id)

    async def list_by_user(self, user_id: uuid.UUID) -> list[PhotoRequest]:
        requests = [r for r in self._store.values() if r.user_id == user_id]
        return sorted(requests, key=lambda r: r.created_at, reverse=True)

    async def list_pending_by_user(self, user_id: uuid.UUID) -> list[PhotoRequest]:
        return [
            r for r in self._store.values() if r.user_id == user_id and r.status == PhotoRequestStatus.PENDING
        ]

    async def create(
        self, user_id: uuid.UUID, requested_by: uuid.UUID | None, message: str | None
    ) -> PhotoRequest:
        request = PhotoRequest(
            id=uuid.uuid4(),
            user_id=user_id,
            requested_by=requested_by,
            message=message,
            status=PhotoRequestStatus.PENDING,
            created_at=datetime.now(UTC),
            fulfilled_at=None,
        )
        self._store[request.id] = request
        return request

    async def update_status(
        self, request_id: uuid.UUID, status: PhotoRequestStatus, fulfilled_at: datetime | None = None
    ) -> PhotoRequest:
        request = self._store[request_id]
        request.status = status
        if fulfilled_at is not None:
            request.fulfilled_at = fulfilled_at
        return request


@pytest.fixture
def repo() -> FakePhotoRequestRepository:
    return FakePhotoRequestRepository()


@pytest.fixture
def service(repo: FakePhotoRequestRepository) -> PhotoRequestService:
    return PhotoRequestService(repo)  # type: ignore[arg-type]


class TestCreateRequest:
    async def test_요청_생성(self, service: PhotoRequestService) -> None:
        user_id = uuid.uuid4()
        requested_by = uuid.uuid4()
        request = await service.create_request(
            user_id=user_id, requested_by=requested_by, message="어릴 적 사진 더 올려주세요"
        )

        assert request.user_id == user_id
        assert request.requested_by == requested_by
        assert request.status == PhotoRequestStatus.PENDING
        assert request.fulfilled_at is None

    async def test_requested_by_없이도_생성_가능(self, service: PhotoRequestService) -> None:
        request = await service.create_request(user_id=uuid.uuid4(), requested_by=None, message=None)
        assert request.requested_by is None

    async def test_message가_300자_초과면_VALIDATION_ERROR(self, service: PhotoRequestService) -> None:
        with pytest.raises(ApiError) as exc_info:
            await service.create_request(user_id=uuid.uuid4(), requested_by=None, message="x" * 301)
        assert exc_info.value.code == "VALIDATION_ERROR"


class TestDismissRequest:
    async def test_pending을_dismissed로_전이(self, service: PhotoRequestService) -> None:
        request = await service.create_request(user_id=uuid.uuid4(), requested_by=None, message=None)

        dismissed = await service.dismiss_request(request.id)

        assert dismissed.status == PhotoRequestStatus.DISMISSED

    async def test_이미_처리된_요청은_CONFLICT(
        self, service: PhotoRequestService, repo: FakePhotoRequestRepository
    ) -> None:
        request = await service.create_request(user_id=uuid.uuid4(), requested_by=None, message=None)
        await service.dismiss_request(request.id)

        with pytest.raises(ApiError) as exc_info:
            await service.dismiss_request(request.id)
        assert exc_info.value.code == "CONFLICT"

    async def test_존재하지_않는_요청은_NOT_FOUND(self, service: PhotoRequestService) -> None:
        with pytest.raises(ApiError) as exc_info:
            await service.dismiss_request(uuid.uuid4())
        assert exc_info.value.code == "NOT_FOUND"


class TestFulfillPendingForUser:
    """photos 모듈 업로드 완료 콜백이 호출하는 자동 충족 경로."""

    async def test_대기중인_요청_전부_fulfilled로_전이(self, service: PhotoRequestService) -> None:
        user_id = uuid.uuid4()
        req1 = await service.create_request(user_id=user_id, requested_by=None, message="1")
        req2 = await service.create_request(user_id=user_id, requested_by=None, message="2")

        fulfilled = await service.fulfill_pending_for_user(user_id)

        assert {r.id for r in fulfilled} == {req1.id, req2.id}
        assert all(r.status == PhotoRequestStatus.FULFILLED for r in fulfilled)
        assert all(r.fulfilled_at is not None for r in fulfilled)

    async def test_다른_사용자_요청은_건드리지_않는다(self, service: PhotoRequestService) -> None:
        user_a = uuid.uuid4()
        user_b = uuid.uuid4()
        await service.create_request(user_id=user_a, requested_by=None, message=None)
        req_b = await service.create_request(user_id=user_b, requested_by=None, message=None)

        await service.fulfill_pending_for_user(user_a)

        assert req_b.status == PhotoRequestStatus.PENDING

    async def test_이미_dismissed된_요청은_건드리지_않는다(self, service: PhotoRequestService) -> None:
        user_id = uuid.uuid4()
        request = await service.create_request(user_id=user_id, requested_by=None, message=None)
        await service.dismiss_request(request.id)

        fulfilled = await service.fulfill_pending_for_user(user_id)

        assert fulfilled == []
        assert request.status == PhotoRequestStatus.DISMISSED

    async def test_대기중인_요청_없으면_빈_목록(self, service: PhotoRequestService) -> None:
        result = await service.fulfill_pending_for_user(uuid.uuid4())
        assert result == []


class TestListRequestsForUser:
    async def test_다른_사용자_요청은_제외(self, service: PhotoRequestService) -> None:
        user_a = uuid.uuid4()
        user_b = uuid.uuid4()
        await service.create_request(user_id=user_a, requested_by=None, message=None)
        await service.create_request(user_id=user_b, requested_by=None, message=None)

        result = await service.list_requests_for_user(user_a)

        assert len(result) == 1
        assert result[0].user_id == user_a
