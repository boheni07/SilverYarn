"""author 모듈의 공개 조합 지점 — family_members/deps.py와 동일한 패턴.

sync 모듈의 UploadPipelineService가 ChapterService가 필요할 때 이 파일만 import한다.
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core_service.core.db import get_db
from core_service.modules.author.application.chapter_service import ChapterService
from core_service.modules.author.infrastructure.chapter_repository import ChapterRepository
from core_service.modules.author.infrastructure.chapter_revision_repository import (
    ChapterRevisionRepository,
)


def get_chapter_service(session: AsyncSession = Depends(get_db)) -> ChapterService:
    return ChapterService(ChapterRepository(session), ChapterRevisionRepository(session))
