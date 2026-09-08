"""SQLAlchemy 2.0 async 엔진/세션 — CONVENTIONS.md §1.3 (비동기 I/O 기본).

⚠️ 엔진은 지연 생성한다. 모듈 임포트 시점에 `create_async_engine()`을 즉시 호출하면
`asyncpg` 미설치·DB 미기동 환경(예: Application 계층만 페이크 Repository로 단위
테스트할 때)에서도 이 파일을 거치는 모든 import가 실패한다 — 실제로 스캐폴딩 검증
중 `tests/modules/users/test_user_service.py`가 이 문제로 깨지는 것을 확인하고 수정했다.
"""

from collections.abc import AsyncGenerator
from functools import lru_cache

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from core_service.core.config import get_settings


class Base(DeclarativeBase):
    """모든 모듈 ORM 모델의 공통 베이스.

    ⚠️ 이 클래스 자체는 모듈에 속하지 않는 순수 인프라이며, 도메인 엔티티를 여기
    정의하지 않는다 (structure.md F-2 정정 취지 — 도메인 엔티티는 각 모듈 domain/에).
    """


@lru_cache
def get_engine() -> AsyncEngine:
    settings = get_settings()
    return create_async_engine(settings.database_url, echo=settings.debug, pool_pre_ping=True)


@lru_cache
def get_session_factory() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(get_engine(), expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession]:
    """FastAPI Depends용 세션 제공자 — 실제 요청 처리 시점에만 엔진이 생성된다.

    ⚠️ **커밋을 반드시 여기서 한다**: 모든 Repository는 `flush()`만 하고 `commit()`을
    호출하지 않는다(의도적 — 하나의 요청 안에서 여러 Repository가 같은 트랜잭션을
    공유하게 하려면 커밋 시점은 세션 소유자인 이 함수만 알아야 한다, invitations
    수락 흐름처럼 두 모듈이 한 트랜잭션을 공유하는 경우가 실제로 있다). `commit()`을
    빼먹으면 `async with session`의 `__aexit__`가 커밋되지 않은 트랜잭션을 그냥
    닫아버려 — Postgres 세션 종료 시 암묵적으로 롤백된다 — 지금까지의 모든 쓰기
    엔드포인트가 실제로는 아무것도 저장하지 못하는 상태였다. sync 파이프라인
    구현 중 실제 커밋 경로를 따라가다 발견했다.
    """
    async with get_session_factory()() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
