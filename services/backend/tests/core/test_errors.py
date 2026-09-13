"""core/errors.py 유닛 테스트 — 표준 에러 응답 + decisions.md #61(I4) 회귀 방지.

발견한 버그: `handle_unexpected`가 예외를 완전히 삼켜 로그도 안 남고 GlitchTip에도
안 보였다(FastAPI가 여기서 처리를 끝내버려 Starlette의 ServerErrorMiddleware까지
안 내려가 sentry-sdk 자동계측이 못 걺). 이 테스트는 로깅 + sentry_sdk.capture_exception
호출을 고정한다 — 다시 조용히 삼키는 회귀가 생기면 여기서 잡힌다.
"""

import logging
from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from core_service.core.errors import ApiError, register_error_handlers


def _client() -> TestClient:
    app = FastAPI()
    register_error_handlers(app)

    @app.get("/boom-api-error")
    async def boom_api_error() -> None:
        raise ApiError("NOT_FOUND", "테스트용 404")

    @app.get("/boom-unexpected")
    async def boom_unexpected() -> None:
        raise ValueError("예상치 못한 오류")

    return TestClient(app, raise_server_exceptions=False)


def test_api_error_returns_mapped_status_and_body() -> None:
    response = _client().get("/boom-api-error")
    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "NOT_FOUND"
    assert body["error"]["message"] == "테스트용 404"


def test_unexpected_exception_returns_500_without_leaking_detail() -> None:
    response = _client().get("/boom-unexpected")
    assert response.status_code == 500
    body = response.json()
    assert body["error"]["code"] == "INTERNAL_ERROR"
    assert body["error"]["details"]["type"] == "ValueError"


def test_unexpected_exception_is_logged(caplog) -> None:  # noqa: ANN001 — pytest fixture
    with caplog.at_level(logging.ERROR, logger="core_service.core.errors"):
        _client().get("/boom-unexpected")
    assert any("처리되지 않은 예외" in record.message for record in caplog.records)


@patch("core_service.core.errors.sentry_sdk.capture_exception")
def test_unexpected_exception_is_sent_to_sentry_sdk(mock_capture: MagicMock) -> None:
    _client().get("/boom-unexpected")
    mock_capture.assert_called_once()
    (captured_exc,) = mock_capture.call_args.args
    assert isinstance(captured_exc, ValueError)
