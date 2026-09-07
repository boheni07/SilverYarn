"""FastAPI app 진입점 (api 프로세스) — 모든 모듈 라우터를 마운트한다.

실행: uvicorn core_service.main:app --reload --port 8000
"""

from fastapi import FastAPI

from core_service.core.config import get_settings
from core_service.core.errors import register_error_handlers
from core_service.core.logging import configure_logging
from core_service.modules.author.api.v1.chapters import router as chapters_router
from core_service.modules.devices.api.v1.devices import router as devices_router
from core_service.modules.family_members.api.v1.family_members import (
    router as family_members_router,
)
from core_service.modules.sync.api.v1.sync import router as sync_router
from core_service.modules.users.api.v1.users import router as users_router

settings = get_settings()
configure_logging(settings.debug)

app = FastAPI(title=settings.app_name, version="0.1.0")
register_error_handlers(app)

app.include_router(users_router, prefix=settings.api_prefix)
app.include_router(devices_router, prefix=settings.api_prefix)
app.include_router(sync_router, prefix=settings.api_prefix)
app.include_router(chapters_router, prefix=settings.api_prefix)
app.include_router(family_members_router, prefix=settings.api_prefix)
# TODO: care/schedule 모듈 API 완성 후 여기 추가


@app.get("/health")
async def health() -> dict[str, str]:
    """헬스체크 — DB 등 의존성 연결 여부는 확장 예정."""
    return {"status": "ok", "service": settings.app_name}
