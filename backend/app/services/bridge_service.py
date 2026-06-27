from datetime import datetime, timezone

from app.repositories.bridge_repository import BridgeRepository
from app.services.edge_bridge_service import dispatch_bridge_tool


class BridgeService:
    READ_TOOLS = frozenset({"list_dir", "read_file", "get_local_network_info"})
    WRITE_TOOLS = frozenset({"write_file"})
    EXEC_TOOLS = frozenset({"run_command", "control_irrigation", "execute_in_app"})
    ALLOWED_TOOLS = READ_TOOLS | WRITE_TOOLS | EXEC_TOOLS

    def __init__(self, repository: BridgeRepository) -> None:
        self._repo = repository

    async def create_pairing_code(self, user_id: str) -> dict:
        code, expires_at = await self._repo.create_pairing_code(user_id)
        return {
            "code": code,
            "expires_at": expires_at.isoformat(),
            "expires_in_seconds": max(
                0, int((expires_at - datetime.now(timezone.utc)).total_seconds())
            ),
        }

    async def pair_device_internal(
        self,
        *,
        user_id: str,
        device_name: str,
        allowed_roots: list[str] | None,
        enable_write_execute: bool = False,
        solution_context: str | None = None,
    ) -> dict:
        device, device_token = await self._repo.create_device_for_user(
            user_id=user_id,
            device_name=device_name,
            allowed_roots=allowed_roots,
            capabilities=["read", "write", "execute"] if enable_write_execute else ["read"],
            solution_context=solution_context,
        )
        return {
            "device_id": str(device.id),
            "device_name": device.device_name,
            "device_token": device_token,
            "bridge_ws_url": "/api/v1/bridge/ws",
            "solution_context": device.solution_context,
        }

    async def pair_device(
        self,
        *,
        code: str,
        device_name: str,
        allowed_roots: list[str] | None,
        enable_write_execute: bool = False,
        solution_context: str | None = None,
    ) -> dict:
        device, device_token = await self._repo.pair_device(
            code=code.strip(),
            device_name=device_name,
            allowed_roots=allowed_roots,
            capabilities=["read", "write", "execute"] if enable_write_execute else ["read"],
            solution_context=solution_context,
        )
        return {
            "device_id": str(device.id),
            "device_name": device.device_name,
            "device_token": device_token,
            "bridge_ws_url": "/api/v1/bridge/ws",
            "solution_context": device.solution_context,
        }

    async def validate_device_session(self, device_token: str) -> dict | None:
        device = await self._repo.get_device_by_token(device_token)
        if device is None:
            return None
        await self._repo.touch_device(device.id)
        return {
            "device_id": str(device.id),
            "user_id": str(device.user_id),
            "device_name": device.device_name,
        }

    async def list_devices(self, user_id: str) -> list[dict]:
        devices = await self._repo.list_devices(user_id)
        return [
            {
                "id": str(device.id),
                "device_name": device.device_name,
                "capabilities": device.capabilities or ["read"],
                "allowed_roots": device.allowed_roots or [],
                "last_seen_at": device.last_seen_at.isoformat() if device.last_seen_at else None,
                "created_at": device.created_at.isoformat(),
            }
            for device in devices
        ]

    async def revoke_device(self, user_id: str, device_id: str) -> bool:
        return await self._repo.revoke_device(user_id, device_id)

    async def ensure_device_for_user(self, user_id: str, device_id: str) -> dict:
        device = await self._repo.get_device_for_user(user_id, device_id)
        if device is None:
            raise ValueError(
                "Bridge device not found. Pair your machine at /bridge and keep `agentnexus-bridge connect` running."
            )
        return {
            "id": str(device.id),
            "device_name": device.device_name,
            "capabilities": device.capabilities or ["read"],
        }

    async def invoke_tool(
        self,
        *,
        user_id: str,
        device_id: str,
        tool: str,
        args: dict,
    ) -> dict:
        if tool not in self.ALLOWED_TOOLS:
            raise ValueError(f"Unknown bridge tool '{tool}'")

        device = await self._repo.get_device_for_user(user_id, device_id)
        if device is None:
            raise KeyError("Device not found")

        self._ensure_device_capability(device, tool)

        timeout_ms = 120_000 if tool in self.WRITE_TOOLS | self.EXEC_TOOLS else 30_000
        result = await dispatch_bridge_tool(
            user_id=user_id,
            device_id=device_id,
            tool=tool,
            args=args,
            timeout_ms=timeout_ms,
        )
        await self._repo.log_audit(
            user_id=user_id,
            device_id=device_id,
            tool_name=tool,
            args=args,
            ok=bool(result.get("ok")),
            error_message=result.get("error"),
        )
        return result

    @staticmethod
    def _ensure_device_capability(device, tool: str) -> None:
        caps = set(device.capabilities or ["read"])
        if tool in BridgeService.READ_TOOLS:
            if caps & {"read", "write", "execute"}:
                return
        if tool in BridgeService.WRITE_TOOLS and "write" in caps:
            return
        if tool in BridgeService.EXEC_TOOLS and "execute" in caps:
            return
        raise ValueError(
            f"Device '{device.device_name}' does not have permission for '{tool}'. "
            "Re-pair with --allow-write or enable write/execute in the web UI."
        )