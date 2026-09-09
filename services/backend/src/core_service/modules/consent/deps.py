"""consent 모듈의 공개 조합 지점 — family_members/deps.py와 동일한 패턴.

온보딩 오케스트레이션(users 생성 → 동의 기록 → devices 등록)이 한 트랜잭션에서
ConsentService를 필요로 할 때 이 파일만 import한다.
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core_service.core.db import get_db
from core_service.modules.consent.application.consent_service import ConsentService
from core_service.modules.consent.infrastructure.consent_log_repository import ConsentLogRepository


def get_consent_service(session: AsyncSession = Depends(get_db)) -> ConsentService:
    return ConsentService(ConsentLogRepository(session))
