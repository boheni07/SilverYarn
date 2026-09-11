"""users 모듈의 공개 조합 지점 — author/deps.py와 동일한 패턴.

sync 모듈의 UploadPipelineService/download 엔드포인트가 UserService가 필요할 때
이 파일만 import한다.
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core_service.core.db import get_db
from core_service.modules.users.application.user_service import UserService
from core_service.modules.users.infrastructure.user_repository import UserRepository


def get_user_service(session: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(UserRepository(session))
