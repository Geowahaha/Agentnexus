import asyncio
import os
import selectors
import sys
from pathlib import Path


def _ensure_runtime() -> None:
    try:
        import pydantic_settings  # noqa: F401
    except ModuleNotFoundError:
        venv_python = Path(__file__).parent / ".venv" / "Scripts" / "python.exe"
        raise SystemExit(
            "Missing backend dependencies. Use the project virtualenv:\n"
            f"  {venv_python} run.py\n"
            "Or on PowerShell:\n"
            "  .\\run.ps1\n"
            "Or activate the venv first:\n"
            "  .\\.venv\\Scripts\\Activate.ps1\n"
            "  python run.py"
        ) from None


_ensure_runtime()

import uvicorn


async def serve() -> None:
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    config = uvicorn.Config("app.main:app", host=host, port=port, loop="asyncio")
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    backend_root = Path(__file__).parent
    if str(backend_root) not in sys.path:
        sys.path.insert(0, str(backend_root))

    if sys.platform == "win32":
        asyncio.run(serve(), loop_factory=lambda: asyncio.SelectorEventLoop(selectors.SelectSelector()))
    else:
        asyncio.run(serve())