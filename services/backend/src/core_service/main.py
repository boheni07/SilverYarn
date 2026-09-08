"""FastAPI app 진입점 (api 프로세스) — 모든 모듈 라우터를 마운트한다.

실행: uvicorn core_service.main:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core_service.core import model_registry  # noqa: F401  (Base.metadata에 전 테이블 등록)
from core_service.core.config import get_settings
from core_service.core.errors import register_error_handlers
from core_service.core.logging import configure_logging
from core_service.modules.author.api.v1.chapters import router as chapters_router
from core_service.modules.care.api.v1.conversation_chunks import (
    router as conversation_chunks_router,
)
from core_service.modules.devices.api.v1.devices import router as devices_router
from core_service.modules.family_members.api.v1.family_members import (
    router as family_members_router,
)
from core_service.modules.invitations.api.v1.invitations import router as invitations_router
from core_service.modules.schedule.api.v1.schedule_items import router as schedule_items_router
from core_service.modules.sync.api.v1.sync import router as sync_router
from core_service.modules.users.api.v1.users import router as users_router

settings = get_settings()
configure_logging(settings.debug)

app = FastAPI(title=settings.app_name, version="0.1.0")
register_error_handlers(app)

# apps/web의 "use client" 컴포넌트가 브라우저에서 직접 보내는 요청을 허용한다 —
# Server Component의 fetch(Node 프로세스 실행)는 CORS 대상이 아니라 이 미들웨어
# 없이도 이미 잘 동작했었다. core/config.py의 CORS_ALLOWED_ORIGINS 참조.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users_router, prefix=settings.api_prefix)
app.include_router(devices_router, prefix=settings.api_prefix)
app.include_router(sync_router, prefix=settings.api_prefix)
app.include_router(chapters_router, prefix=settings.api_prefix)
app.include_router(family_members_router, prefix=settings.api_prefix)
app.include_router(invitations_router, prefix=settings.api_prefix)
app.include_router(conversation_chunks_router, prefix=settings.api_prefix)
app.include_router(schedule_items_router, prefix=settings.api_prefix)


@app.get("/health")
async def health() -> dict[str, str]:
    """헬스체크 — DB 등 의존성 연결 여부는 확장 예정."""
    return {"status": "ok", "service": settings.app_name}
