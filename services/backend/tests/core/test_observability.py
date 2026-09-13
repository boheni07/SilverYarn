"""core/observability.py 유닛 테스트 — decisions.md #61(I4).

실제 GlitchTip/네트워크 없이 "DSN 없으면 꺼짐" 원칙만 검증한다(PII_KEK와 동일
패턴). 실제 에러 캡처·Prometheus 스크레이프는 로컬 Docker 스택으로 수기 검증.
"""

from unittest.mock import MagicMock, patch

from core_service.core.config import Settings
from core_service.core.observability import init_error_tracking, instrument_metrics


def _settings(dsn: str = "") -> Settings:
    return Settings(_env_file=None, OBS_GLITCHTIP_DSN=dsn)  # type: ignore[call-arg]


@patch("core_service.core.observability.sentry_sdk.init")
def test_no_dsn_skips_init(mock_init: MagicMock) -> None:
    init_error_tracking(_settings(dsn=""))
    mock_init.assert_not_called()


@patch("core_service.core.observability.sentry_sdk.init")
def test_dsn_set_initializes_sentry_sdk(mock_init: MagicMock) -> None:
    init_error_tracking(_settings(dsn="https://public@glitchtip.local/1"))
    mock_init.assert_called_once()
    _, kwargs = mock_init.call_args
    assert kwargs["dsn"] == "https://public@glitchtip.local/1"
    assert kwargs["traces_sample_rate"] == 0.0
    assert kwargs["send_default_pii"] is False


def test_instrument_metrics_exposes_endpoint() -> None:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    app = FastAPI()
    instrument_metrics(app)

    with TestClient(app) as client:
        response = client.get("/metrics")
    assert response.status_code == 200
    assert b"python_info" in response.content or b"# HELP" in response.content
