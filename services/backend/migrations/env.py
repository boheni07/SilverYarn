"""Alembic env — DB_ 환경변수(CONVENTIONS.md §4)로 접속, core_service.core.db.Base 메타데이터 사용."""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# 모든 모듈의 ORM 모델을 한 곳에서 import — Base.metadata에 전 테이블을 등록한다.
# 개별 진입점마다 모델 import 목록을 따로 유지하다 worker.py에서 실제로 하나를
# 빠뜨려 FK 해석 오류가 난 적이 있다(core/model_registry.py 문서 참조).
from core_service.core import model_registry  # noqa: F401
from core_service.core.config import get_settings
from core_service.core.db import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.database_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
