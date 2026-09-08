"""Whisper Large-v3 온프레미스 재전사 클라이언트 — design.md §2.11 3단계.

⚠️ REST 계약 가정: `POST {STT_ENDPOINT}/transcribe`에 `{"audio_ref": "<MinIO 키>"}`를
보내면 `{"text": "..."}`를 반환한다고 가정했다 — 실제 온프레미스 Whisper 서비스
배포 시 이 클래스만 교체.
"""

import httpx

from core_service.core.config import get_settings


class STTClient:
    def __init__(self, endpoint: str | None = None, timeout: float = 30.0):
        self._endpoint = endpoint or get_settings().stt_endpoint
        self._timeout = timeout

    async def transcribe(self, raw_audio_ref: str) -> str:
        """원본 음성(MinIO 참조)을 고정밀 재전사한다. 실패 시 예외를 그대로 던진다 —
        best-effort 처리(실패해도 파이프라인 계속 진행)는 호출자(UploadPipelineService)
        책임이다."""
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(f"{self._endpoint}/transcribe", json={"audio_ref": raw_audio_ref})
            response.raise_for_status()
            return response.json()["text"]
