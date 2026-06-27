from psycopg_pool import AsyncConnectionPool

from app.core.config import settings
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

_pool: AsyncConnectionPool | None = None
_checkpointer: AsyncPostgresSaver | None = None


def get_checkpoint_dsn() -> str:
    return settings.database_url.replace("postgresql+asyncpg://", "postgresql://")


async def init_checkpointer() -> AsyncPostgresSaver:
    global _pool, _checkpointer
    if _checkpointer is not None:
        return _checkpointer

    _pool = AsyncConnectionPool(
        get_checkpoint_dsn(),
        kwargs={"autocommit": True, "prepare_threshold": 0},
        open=False,
    )
    await _pool.open()
    _checkpointer = AsyncPostgresSaver(conn=_pool)
    await _checkpointer.setup()
    return _checkpointer


async def close_checkpointer() -> None:
    global _pool, _checkpointer
    if _pool is not None:
        await _pool.close()
    _pool = None
    _checkpointer = None


def get_checkpointer() -> AsyncPostgresSaver:
    if _checkpointer is None:
        raise RuntimeError("Checkpointer is not initialized. FastAPI lifespan may not have run.")
    return _checkpointer