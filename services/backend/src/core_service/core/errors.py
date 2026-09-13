"""표준 응답/에러 포맷 — design.md §4.1, sync-contract.md §6.

성공: {"data": {...}}
목록: {"data": [...], "pagination": {...}}
에러: {"error": {"code": ..., "message": ..., "details": {...}}}
"""

import logging
from typing import Any

import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

# design.md §4.1 표준 에러 코드 + sync-contract.md §6 (429/413)
# ⚠️ fastapi.status의 이름 있는 상수 대신 정수를 직접 쓴다 — starlette 버전에 따라
# HTTP_413_REQUEST_ENTITY_TOO_LARGE/HTTP_422_UNPROCESSABLE_ENTITY 같은 상수명이
# 바뀌는 것을 스캐폴딩 검증 중 확인했다(신버전엔 *_CONTENT로 개명). 표준 코드값은
# 안정적이므로 정수 리터럴이 더 견고하다.
ERROR_STATUS_MAP: dict[str, int] = {
    "VALIDATION_ERROR": 400,
    "UNAUTHORIZED": 401,
    "FORBIDDEN": 403,
    "NOT_FOUND": 404,
    "CONFLICT": 409,
    "PAYLOAD_TOO_LARGE": 413,
    "SYNC_CHECKSUM_MISMATCH": 422,
    "RATE_LIMITED": 429,
    "INTERNAL_ERROR": 500,
}


class ApiError(Exception):
    """표준 에러 코드로 응답을 내리기 위한 도메인 예외.

    Application 레이어에서 `raise ApiError("NOT_FOUND", "사용자를 찾을 수 없습니다")`
    형태로 사용하고, api 레이어는 이 예외를 직접 알 필요 없이 아래 핸들러가 처리한다.
    """

    def __init__(self, code: str, message: str, details: dict[str, Any] | None = None):
        if code not in ERROR_STATUS_MAP:
            raise ValueError(f"Unknown error code: {code}")
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def handle_api_error(_: Request, exc: ApiError) -> JSONResponse:
        return JSONResponse(
            status_code=ERROR_STATUS_MAP[exc.code],
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                }
            },
        )

    @app.exception_handler(Exception)
    async def handle_unexpected(_: Request, exc: Exception) -> JSONResponse:
        # ⚠️ decisions.md #61(I4) 도입 전에는 이 핸들러가 예외를 그냥 삼켰다 — 로그도
        # 안 남고 GlitchTip에도 안 보였다(FastAPI가 여기서 완전히 처리해 버려
        # Starlette의 ServerErrorMiddleware까지 안 내려가고, sentry-sdk의 자동
        # 계측은 그 미들웨어에서 걸리기 때문). 명시적으로 로깅 + 캡처한다.
        # `sentry_sdk.capture_exception`은 `init_error_tracking`이 DSN 없어서
        # 호출 안 됐어도(core/observability.py) 안전한 no-op이다.
        logger.exception("처리되지 않은 예외 — path=%s", _.url.path)
        sentry_sdk.capture_exception(exc)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "예기치 않은 오류가 발생했습니다.",
                    "details": {"type": type(exc).__name__},
                }
            },
        )
