"""어르신 계정 전체 삭제(erasure) 오케스트레이션 — decisions.md #56(2026-09-13, Q5).

CTO가 "5개 저장소 통합 삭제"로 지목했던 항목을 조사해 보니, Postgres 쪽은 이미
거의 모든 테이블이 `user_id ... ON DELETE CASCADE`로 걸려 있어(`UserRepository.delete`
docstring 참조) `DELETE FROM users` 한 줄로 끝난다 — 실제로 오케스트레이션이
필요한 건 **Postgres 밖 3곳**(Qdrant·Neo4j·MinIO)뿐이다.

## 순서와 그 이유 (실패 시 재시도 안전성)
외부 저장소(Qdrant·Neo4j·MinIO) 삭제를 **먼저**, Postgres `DELETE FROM users`를
**마지막**에 한다. 외부 저장소 삭제는 전부 멱등(이미 지워진 걸 또 지워도 안전)이라,
중간에 실패해도 `erase_user()`를 통째로 재호출하면 안전하게 이어서 끝낼 수 있다.
반대로 Postgres를 먼저 지우면 사용자 행이 사라져 재시도 시점에 "이 사용자가
어떤 사진을 갖고 있었는지" 같은 정보를 잃어버려 외부 저장소 정리가 불가능해진다.

`deletion_records`(감사 로그, `core/deletion_log.py`)는 `users` 삭제와 **같은
트랜잭션**에 넣는다 — 그래야 "삭제됐다는 기록은 있는데 실제로는 실패했다" 또는
그 반대의 불일치가 안 생긴다.
"""

import logging
import uuid

from core_service.core.clients.graph_client import GraphClient
from core_service.core.clients.storage_client import StorageClient
from core_service.core.clients.vectordb_client import VectorDBClient
from core_service.core.deletion_log import DeletionRecordRepository
from core_service.core.errors import ApiError
from core_service.modules.photos.infrastructure.photo_repository import PhotoRepository
from core_service.modules.users.infrastructure.user_repository import UserRepository

logger = logging.getLogger(__name__)

_PURGED_STORES = ["qdrant", "neo4j", "minio", "postgres"]


class UserErasureService:
    def __init__(
        self,
        user_repo: UserRepository,
        photo_repo: PhotoRepository,
        deletion_record_repo: DeletionRecordRepository,
        vectordb_client: VectorDBClient,
        graph_client: GraphClient,
        storage_client: StorageClient,
    ):
        self._users = user_repo
        self._photos = photo_repo
        self._deletion_records = deletion_record_repo
        self._vectordb = vectordb_client
        self._graph = graph_client
        self._storage = storage_client

    async def erase_user(self, user_id: uuid.UUID, *, requested_by: uuid.UUID | None, reason: str) -> None:
        user = await self._users.get_by_id(user_id)
        if user is None:
            raise ApiError("NOT_FOUND", f"사용자({user_id})를 찾을 수 없습니다.")

        # Postgres가 곧 이 목록 자체를 지워버리므로(cascade) MinIO 정리에 필요한
        # storage_ref는 먼저 읽어 둔다.
        photos = await self._photos.list_by_user(user_id)

        await self._vectordb.delete_user_vectors(user_id)
        await self._graph.delete_user_nodes(user_id)
        for photo in photos:
            await self._storage.remove_object(photo.storage_ref)

        await self._deletion_records.record(
            user_id=user_id, requested_by=requested_by, reason=reason, purged_stores=_PURGED_STORES
        )
        await self._users.delete(user_id)
        logger.info("사용자 삭제(erasure) 완료 — user_id=%s, photos=%d건", user_id, len(photos))
