"""MinIO(S3 호환) Object Storage 클라이언트 — sync-contract.md §4 "사진 업로드 —
Presigned URL 흐름"의 서버측.

이 디렉터리의 다른 클라이언트(STT/Embedding/LLM)와 달리 MinIO는 실제로
로컬 docker-compose에 떠 있고(infra/docker-compose.yml) SDK 계약도 추정이 아니다
— Qdrant/Neo4j와 같은 부류(실 SDK 확정)로 취급한다.

⚠️ `presigned_put_object()`는 로컬 HMAC 서명 계산만 하고 네트워크 호출을 하지
않는다(minio-py 구현) — async 핸들러에서 그대로 불러도 이벤트 루프를 막지 않는다.
반면 `bucket_exists`/`make_bucket`은 실제 HTTP 요청이라 `asyncio.to_thread`로
감쌌다.
"""

import asyncio
from datetime import timedelta

from minio import Minio
from minio.error import S3Error

from core_service.core.config import get_settings


class StorageClient:
    def __init__(self) -> None:
        settings = get_settings()
        self._client = Minio(
            settings.storage_endpoint,
            access_key=settings.storage_access_key,
            secret_key=settings.storage_secret_key,
            secure=settings.storage_secure,
        )
        self._bucket = settings.storage_bucket_photos

    async def ensure_bucket(self) -> None:
        """버킷이 없으면 만든다 — 매 업로드 요청마다 부를 필요는 없지만(네트워크 호출),
        지금은 별도 앱 startup 훅이 없어 PhotoService가 최초 요청 시점에 호출한다."""

        def _ensure() -> None:
            if not self._client.bucket_exists(self._bucket):
                self._client.make_bucket(self._bucket)

        await asyncio.to_thread(_ensure)

    def presigned_put_url(self, object_name: str, expires: timedelta = timedelta(minutes=15)) -> str:
        """sync-contract.md §4 1단계 응답의 `upload_url` — 15분 만료 문서 스펙 그대로."""
        return self._client.presigned_put_object(self._bucket, object_name, expires=expires)

    def presigned_get_url(self, object_name: str, expires: timedelta = timedelta(minutes=15)) -> str:
        """apps/web 사진 갤러리가 실제로 이미지를 보여줄 때 쓴다 — 버킷을 public-read로
        열지 않고(가족 사진은 PII에 준하는 민감 데이터) 매 조회 응답마다 짧게 만료되는
        서명 URL을 새로 발급한다. presigned_put_url과 마찬가지로 로컬 HMAC 서명
        계산만 하고 네트워크 호출은 없다."""
        return self._client.presigned_get_object(self._bucket, object_name, expires=expires)

    async def remove_object(self, object_name: str) -> None:
        """photos orphan cleanup(sync-contract.md §4)용 — pending_upload로 24시간
        넘게 남은 행을 지울 때, 실제로 MinIO에 파일이 올라갔을 수도 있는 경우까지
        같이 정리한다. 대부분은 presigned URL을 아예 쓰지 않아(15분 만료 후 방치)
        객체가 애초에 없는 게 정상 케이스라 NoSuchKey는 에러로 취급하지 않는다."""

        def _remove() -> None:
            try:
                self._client.remove_object(self._bucket, object_name)
            except S3Error as exc:
                if exc.code != "NoSuchKey":
                    raise

        await asyncio.to_thread(_remove)
