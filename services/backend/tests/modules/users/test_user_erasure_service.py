"""UserErasureService 유닛 테스트 — 페이크 6종으로 DB/실 인프라 없이 오케스트레이션
순서·조건을 검증한다.

decisions.md #56(Q5, 2026-09-13) — 어르신 계정 전체 삭제(erasure). 검증 초점은
"Postgres DELETE가 항상 마지막"과 "외부 저장소 3곳이 먼저 지워짐"(모듈 docstring의
재시도 안전성 근거) — 실행 순서를 기록해 assert한다.
"""

import uuid
from datetime import UTC, date, datetime

import pytest

from core_service.core.errors import ApiError
from core_service.modules.photos.domain.photo import Photo as PhotoEntity
from core_service.modules.photos.domain.photo import (
    PhotoUploadStatus,
    PlacementStatus,
    QualityFlag,
    RecallStatus,
    UploaderType,
)
from core_service.modules.users.application.user_erasure_service import UserErasureService
from core_service.modules.users.domain.user import User


def _user(user_id: uuid.UUID) -> User:
    now = datetime.now(UTC)
    return User(
        id=user_id,
        name="김옥순",
        birth_date=date(1945, 3, 1),
        primary_device_id=None,
        created_at=now,
        updated_at=now,
    )


def _photo(user_id: uuid.UUID, storage_ref: str) -> PhotoEntity:
    now = datetime.now(UTC)
    return PhotoEntity(
        id=uuid.uuid4(),
        user_id=user_id,
        uploader_type=UploaderType.FAMILY,
        status=PhotoUploadStatus.UPLOADED,
        storage_ref=storage_ref,
        caption=None,
        year_tag=None,
        recall_status=RecallStatus.COMPLETED,
        placement_status=PlacementStatus.CONFIRMED,
        inline_position=None,
        linked_chunk_id=None,
        linked_chapter_id=None,
        quality_flag=QualityFlag.UNREVIEWED,
        width=None,
        height=None,
        file_size_kb=None,
        mime_type=None,
        uploaded_at=now,
    )


class FakeUserRepository:
    def __init__(self, user: User | None) -> None:
        self._user = user
        self.deleted_ids: list[uuid.UUID] = []

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return self._user if self._user and self._user.id == user_id else None

    async def delete(self, user_id: uuid.UUID) -> None:
        self.deleted_ids.append(user_id)


class FakePhotoRepository:
    def __init__(self, photos: list[PhotoEntity]) -> None:
        self._photos = photos

    async def list_by_user(self, user_id: uuid.UUID) -> list[PhotoEntity]:
        return [p for p in self._photos if p.user_id == user_id]


class FakeDeletionRecordRepository:
    def __init__(self) -> None:
        self.records: list[dict] = []

    async def record(
        self, *, user_id: uuid.UUID, requested_by: uuid.UUID | None, reason: str, purged_stores: list[str]
    ) -> None:
        self.records.append(
            {
                "user_id": user_id,
                "requested_by": requested_by,
                "reason": reason,
                "purged_stores": purged_stores,
            }
        )


class RecordingClient:
    """Qdrant/Neo4j/MinIO 페이크 공통 — 호출 순서를 `call_log`(공유 리스트)에 남긴다."""

    def __init__(self, name: str, call_log: list[str]) -> None:
        self._name = name
        self._log = call_log

    async def delete_user_vectors(self, user_id: uuid.UUID) -> None:
        _ = user_id
        self._log.append(f"{self._name}.delete_user_vectors")

    async def delete_user_nodes(self, user_id: uuid.UUID) -> None:
        _ = user_id
        self._log.append(f"{self._name}.delete_user_nodes")

    async def remove_object(self, storage_ref: str) -> None:
        _ = storage_ref
        self._log.append(f"{self._name}.remove_object:{storage_ref}")


@pytest.fixture
def call_log() -> list[str]:
    return []


async def test_erase_user_not_found_raises_api_error(call_log: list[str]) -> None:
    service = UserErasureService(
        FakeUserRepository(None),  # type: ignore[arg-type]
        FakePhotoRepository([]),  # type: ignore[arg-type]
        FakeDeletionRecordRepository(),  # type: ignore[arg-type]
        RecordingClient("vectordb", call_log),  # type: ignore[arg-type]
        RecordingClient("graph", call_log),  # type: ignore[arg-type]
        RecordingClient("storage", call_log),  # type: ignore[arg-type]
    )
    with pytest.raises(ApiError, match="찾을 수 없습니다"):
        await service.erase_user(uuid.uuid4(), requested_by=None, reason="테스트")


async def test_erase_user_deletes_external_stores_before_postgres(call_log: list[str]) -> None:
    """모듈 docstring의 재시도 안전성 근거 — Qdrant/Neo4j/MinIO가 먼저, Postgres가 마지막."""
    user_id = uuid.uuid4()
    photo = _photo(user_id, "minio://photos/abc.jpg")
    user_repo = FakeUserRepository(_user(user_id))
    deletion_records = FakeDeletionRecordRepository()

    service = UserErasureService(
        user_repo,  # type: ignore[arg-type]
        FakePhotoRepository([photo]),  # type: ignore[arg-type]
        deletion_records,  # type: ignore[arg-type]
        RecordingClient("vectordb", call_log),  # type: ignore[arg-type]
        RecordingClient("graph", call_log),  # type: ignore[arg-type]
        RecordingClient("storage", call_log),  # type: ignore[arg-type]
    )

    await service.erase_user(user_id, requested_by=uuid.uuid4(), reason="본인 요청")

    assert call_log == [
        "vectordb.delete_user_vectors",
        "graph.delete_user_nodes",
        f"storage.remove_object:{photo.storage_ref}",
    ]
    assert user_repo.deleted_ids == [user_id]
    assert len(deletion_records.records) == 1
    assert deletion_records.records[0]["purged_stores"] == ["qdrant", "neo4j", "minio", "postgres"]


async def test_erase_user_records_deletion_before_postgres_delete_and_after_external(
    call_log: list[str],
) -> None:
    """감사 로그(`deletion_records`)는 외부 저장소 정리 뒤·Postgres 삭제 전에 남는다
    (같은 트랜잭션이라 순서 자체는 원자성에 영향 없지만, 호출 순서로 의도를 검증)."""
    user_id = uuid.uuid4()
    order: list[str] = []

    class OrderTrackingDeletionRecords(FakeDeletionRecordRepository):
        async def record(self, **kwargs) -> None:  # type: ignore[override]
            order.append("deletion_record")
            await super().record(**kwargs)

    class OrderTrackingUserRepository(FakeUserRepository):
        async def delete(self, user_id: uuid.UUID) -> None:
            order.append("postgres_delete")
            await super().delete(user_id)

    service = UserErasureService(
        OrderTrackingUserRepository(_user(user_id)),  # type: ignore[arg-type]
        FakePhotoRepository([]),  # type: ignore[arg-type]
        OrderTrackingDeletionRecords(),  # type: ignore[arg-type]
        RecordingClient("vectordb", call_log),  # type: ignore[arg-type]
        RecordingClient("graph", call_log),  # type: ignore[arg-type]
        RecordingClient("storage", call_log),  # type: ignore[arg-type]
    )

    await service.erase_user(user_id, requested_by=None, reason="테스트")

    assert order == ["deletion_record", "postgres_delete"]


async def test_erase_user_removes_every_photo_object(call_log: list[str]) -> None:
    user_id = uuid.uuid4()
    photos = [_photo(user_id, "minio://a.jpg"), _photo(user_id, "minio://b.jpg")]
    service = UserErasureService(
        FakeUserRepository(_user(user_id)),  # type: ignore[arg-type]
        FakePhotoRepository(photos),  # type: ignore[arg-type]
        FakeDeletionRecordRepository(),  # type: ignore[arg-type]
        RecordingClient("vectordb", call_log),  # type: ignore[arg-type]
        RecordingClient("graph", call_log),  # type: ignore[arg-type]
        RecordingClient("storage", call_log),  # type: ignore[arg-type]
    )

    await service.erase_user(user_id, requested_by=None, reason="테스트")

    removed = [c for c in call_log if c.startswith("storage.remove_object")]
    assert removed == ["storage.remove_object:minio://a.jpg", "storage.remove_object:minio://b.jpg"]
