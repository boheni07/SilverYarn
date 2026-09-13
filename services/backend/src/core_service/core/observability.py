"""관측 스택 배선 — decisions.md #61(2026-09-12 사용자 결정, I4).

Sentry SaaS는 I1(PII 외부유출 금지) 원칙상 사용 불가해 self-hosted GlitchTip(Sentry
프로토콜 호환)으로 에러를 리포팅하고, Prometheus가 스크레이프할 `/metrics`를 노출한다.
로그(JSON → Grafana Alloy → Loki)는 core/logging.py가 담당(여긴 에러·메트릭만).

두 기능 모두 "설정 없으면 꺼짐" 원칙(PII_KEK와 동일) — 로컬에서 관측 컨테이너
없이도 앱이 그대로 뜬다.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import sentry_sdk
from prometheus_fastapi_instrumentator import Instrumentator
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

from core_service.core.config import Settings

if TYPE_CHECKING:
    from fastapi import FastAPI


def init_error_tracking(settings: Settings) -> None:
    """`OBS_GLITCHTIP_DSN`이 설정된 경우에만 sentry-sdk를 초기화한다.

    FastAPI 앱 인스턴스 생성 **전에** 호출해야 Starlette/FastAPI 미들웨어 계측이
    자동으로 걸린다(sentry-sdk 공식 권장 순서). `traces_sample_rate=0`으로 APM
    트레이싱은 끄고 에러 캡처만 쓴다 — 이번 라운드 범위는 에러 추적까지다.
    """
    if not settings.obs_glitchtip_dsn:
        return
    sentry_sdk.init(
        dsn=settings.obs_glitchtip_dsn,
        integrations=[StarletteIntegration(), FastApiIntegration()],
        traces_sample_rate=0.0,
        send_default_pii=False,  # PII 자유텍스트가 에러 컨텍스트에 섞이지 않도록
        environment="local-dev",
    )


def instrument_metrics(app: FastAPI) -> None:
    """`GET /metrics`(Prometheus 텍스트 포맷)를 노출한다. DSN과 달리 항상 켠다 —
    스크레이프 안 해도(Prometheus 컨테이너가 없어도) 비용이 없고, 나중에 관측
    스택을 붙일 때 앱 재배포 없이 바로 스크레이프 대상이 될 수 있어야 하기 때문."""
    Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)
