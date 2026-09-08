"""photo_requests 모듈의 공개 조합 지점 — devices/deps.py, family_members/deps.py와
동일한 패턴.

photos 모듈이 업로드 완료 시 "이 사용자의 대기 중인 사진 요청을 충족 처리"하려면
이 파일만 import한다(photo_requests 테이블/Repository를 직접 건드리지 않음).
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core_service.core.db import get_db
from core_service.modules.photo_requests.application.photo_request_service import PhotoRequestService
from core_service.modules.photo_requests.infrastructure.photo_request_repository import (
    PhotoRequestRepository,
)


def get_photo_request_service(session: AsyncSession = Depends(get_db)) -> PhotoRequestService:
    return PhotoRequestService(PhotoRequestRepository(session))
