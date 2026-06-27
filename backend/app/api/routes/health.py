from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from sqlalchemy import text

from app.core.checkpoint import get_checkpointer
from app.core.config import settings
from app.core.database import async_session_maker, engine

router = APIRouter()


@router.get("/health")
async def health_check():
    checks = {
        "app": settings.app_name,
        "version": settings.app_version,
        "db": "unknown",
        "checkpointer": "unknown",
    }
    overall_ok = True

    # DB ping
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["db"] = "ok"
    except Exception as exc:
        checks["db"] = f"fail: {type(exc).__name__}"
        overall_ok = False

    # Checkpointer (LangGraph persistent state)
    try:
        cp = get_checkpointer()
        # lightweight touch
        _ = cp  # already initialized in lifespan if healthy
        checks["checkpointer"] = "ok"
    except Exception as exc:
        checks["checkpointer"] = f"fail: {type(exc).__name__}"
        overall_ok = False

    payload = {
        "status": "ok" if overall_ok else "degraded",
        **checks,
    }
    http_status = status.HTTP_200_OK if overall_ok else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(payload, status_code=http_status)