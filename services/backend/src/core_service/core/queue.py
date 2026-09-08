"""arq 잡 큐 연결 — sync-contract.md §2 비동기 처리 계약의 api 프로세스측.

FastAPI 요청마다 새 Redis 커넥션을 만들지 않도록 프로세스 전역에 풀 1개를
지연 생성해 재사용한다(락으로 동시 생성 경쟁 방지).
"""

import asyncio

from arq import create_pool
from arq.connections import ArqRedis, RedisSettings

from core_service.core.config import get_settings

_pool: ArqRedis | None = None
_pool_lock = asyncio.Lock()


async def get_arq_pool() -> ArqRedis:
    """FastAPI Depends용 — `pool: ArqRedis = Depends(get_arq_pool)`."""
    global _pool
    if _pool is None:
        async with _pool_lock:
            if _pool is None:
                settings = get_settings()
                _pool = await create_pool(RedisSettings(host=settings.redis_host, port=settings.redis_port))
    return _pool
