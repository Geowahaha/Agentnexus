import asyncio
import logging
import sys
import time
from pathlib import Path

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.api import api_router
from app.api.v1.obolla_mcp import router as obolla_mcp_router
from app.core.checkpoint import close_checkpointer, init_checkpointer
from app.core.config import settings

from app.smart_farm.mqtt_credentials import ensure_ingest_service_account
from app.smart_farm.mqtt_subscriber import start_smart_farm_background_tasks, stop_smart_farm_background_tasks


# Production-grade basic logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("agentnexus")


class AccessLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        duration_ms = int((time.time() - start) * 1000)
        logger.info(
            "%s %s %s %dms",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response


def _ensure_smart_farm_storage() -> None:
    auth_dir = Path("/app/data/mosquitto")
    auth_dir.mkdir(parents=True, exist_ok=True)
    passwd = auth_dir / "passwd"
    acl = auth_dir / "acl"
    if not passwd.is_file():
        passwd.write_text("", encoding="utf-8")
    if not acl.is_file():
        acl.write_text("", encoding="utf-8")
    passwd.chmod(0o600)
    acl.chmod(0o600)
    if settings.smart_farm_mqtt_password:
        ensure_ingest_service_account(settings.smart_farm_mqtt_password)


@asynccontextmanager
async def lifespan(_: FastAPI):
    _ensure_smart_farm_storage()
    await init_checkpointer()
    bg_tasks = await start_smart_farm_background_tasks()
    yield
    await stop_smart_farm_background_tasks(bg_tasks)
    await close_checkpointer()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Access logging (after CORS so it sees final responses)
app.add_middleware(AccessLogMiddleware)

app.include_router(api_router, prefix=settings.api_prefix)

# Public MCP HTTP endpoint at clean path (for local AIs, Claude Desktop, Cursor, etc.)
# Supports JSON-RPC: initialize, tools/list, tools/call (apply_agent_ready_fix)
app.include_router(obolla_mcp_router, prefix="")


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": f"Welcome to {settings.app_name}"}