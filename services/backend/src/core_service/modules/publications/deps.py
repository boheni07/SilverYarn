"""publications 모듈의 공개 조합 지점 — family_members/deps.py와 동일한 패턴."""

from arq.connections import ArqRedis
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core_service.core.db import get_db
from core_service.core.queue import get_arq_pool
from core_service.modules.author.application.chapter_service import ChapterService
from core_service.modules.author.deps import get_chapter_service
from core_service.modules.publications.application.publication_service import PublicationService
from core_service.modules.publications.infrastructure.publication_repository import (
    PublicationRepository,
)


def get_publication_service(
    session: AsyncSession = Depends(get_db),
    chapter_service: ChapterService = Depends(get_chapter_service),
    pool: ArqRedis = Depends(get_arq_pool),
) -> PublicationService:
    return PublicationService(PublicationRepository(session), chapter_service, pool)
