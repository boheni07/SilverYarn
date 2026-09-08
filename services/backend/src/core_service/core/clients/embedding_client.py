"""BGE-M3 임베딩 클라이언트 — design.md §2.4 RAG 파이프라인, decisions.md 확정 모델.

⚠️ REST 계약 가정: `POST {EMBEDDING_ENDPOINT}/embed`에 `{"text": "..."}`를 보내면
`{"embedding": [float, ...]}`를 반환한다고 가정했다.
"""

import httpx

from core_service.core.config import get_settings


class EmbeddingClient:
    def __init__(self, endpoint: str | None = None, timeout: float = 15.0):
        self._endpoint = endpoint or get_settings().embedding_endpoint
        self._timeout = timeout

    async def embed(self, text: str) -> list[float]:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(f"{self._endpoint}/embed", json={"text": text})
            response.raise_for_status()
            return response.json()["embedding"]
