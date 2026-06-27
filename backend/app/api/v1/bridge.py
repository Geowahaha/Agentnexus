from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.core.config import settings
from app.core.deps import get_bridge_service
from app.services.bridge_service import BridgeService

router = APIRouter()


class PairingCodeResponse(BaseModel):
    code: str
    expires_at: str
    expires_in_seconds: int


class PairDeviceRequest(BaseModel):
    code: str = Field(..., min_length=6, max_length=6)
    device_name: str = Field(..., min_length=1, max_length=120)
    allowed_roots: list[str] | None = None
    enable_write_execute: bool = Field(
        default=False,
        description="Allow write_file and run_command (requires terminal consent per action)",
    )
    solution_context: str | None = Field(
        None,
        description="Optional context like skill slug or solution name to associate this device with a specific solution",
    )


class PairDeviceResponse(BaseModel):
    device_id: str
    device_name: str
    device_token: str
    bridge_ws_url: str


class InternalPairDeviceRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    device_name: str = Field(..., min_length=1, max_length=120)
    allowed_roots: list[str] | None = None
    enable_write_execute: bool = False
    solution_context: str | None = None


class DeviceSessionRequest(BaseModel):
    device_token: str


class DeviceSessionResponse(BaseModel):
    device_id: str
    user_id: str
    device_name: str


class BridgeDeviceResponse(BaseModel):
    id: str
    device_name: str
    capabilities: list[str]
    allowed_roots: list[str]
    last_seen_at: str | None
    created_at: str


class InvokeToolRequest(BaseModel):
    tool: str = Field(..., min_length=1)
    args: dict = Field(default_factory=dict)


@router.post("/pairing-codes", response_model=PairingCodeResponse)
async def create_pairing_code(
    current_user: User = Depends(get_current_user),
    service: BridgeService = Depends(get_bridge_service),
) -> PairingCodeResponse:
    payload = await service.create_pairing_code(current_user.id)
    return PairingCodeResponse(**payload)


@router.post("/internal/pair", response_model=PairDeviceResponse)
async def internal_pair_device(
    request: InternalPairDeviceRequest,
    x_bridge_secret: str | None = Header(default=None, alias="X-Bridge-Secret"),
    service: BridgeService = Depends(get_bridge_service),
) -> PairDeviceResponse:
    expected = settings.internal_notify_secret
    if not expected or x_bridge_secret != expected:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    payload = await service.pair_device_internal(
        user_id=request.user_id,
        device_name=request.device_name,
        allowed_roots=request.allowed_roots,
        enable_write_execute=request.enable_write_execute,
        solution_context=request.solution_context,
    )
    return PairDeviceResponse(**payload)


@router.post("/pair", response_model=PairDeviceResponse)
async def pair_device(
    request: PairDeviceRequest,
    service: BridgeService = Depends(get_bridge_service),
) -> PairDeviceResponse:
    try:
        payload = await service.pair_device(
            code=request.code,
            device_name=request.device_name,
            allowed_roots=request.allowed_roots,
            enable_write_execute=request.enable_write_execute,
            solution_context=request.solution_context,
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail="Invalid pairing code. Generate a fresh code on the agent /bridge page and run install immediately.",
        ) from exc
    except ValueError as exc:
        message = str(exc)
        if message == "Pairing code expired":
            message = (
                "Pairing code expired. Generate a NEW code on the agent /bridge page "
                "and run install within 30 minutes."
            )
        elif message == "Pairing code already used":
            message = (
                "Pairing code already used. Generate a NEW code on the agent /bridge page."
            )
        raise HTTPException(status_code=400, detail=message) from exc
    return PairDeviceResponse(**payload)


@router.post("/device-session", response_model=DeviceSessionResponse)
async def device_session(
    request: DeviceSessionRequest,
    x_bridge_secret: str | None = Header(default=None, alias="X-Bridge-Secret"),
    service: BridgeService = Depends(get_bridge_service),
) -> DeviceSessionResponse:
    expected = settings.internal_notify_secret
    if not expected or x_bridge_secret != expected:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    session = await service.validate_device_session(request.device_token)
    if session is None:
        raise HTTPException(status_code=401, detail="Invalid device token")
    return DeviceSessionResponse(**session)


@router.get("/devices", response_model=list[BridgeDeviceResponse])
async def list_devices(
    current_user: User = Depends(get_current_user),
    service: BridgeService = Depends(get_bridge_service),
) -> list[BridgeDeviceResponse]:
    try:
        items = await service.list_devices(current_user.id)
        return [BridgeDeviceResponse(**item) for item in items]
    except Exception:
        # Return empty on error instead of 500 (e.g. no bridge table or service down)
        return []


@router.delete("/devices/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_device(
    device_id: str,
    current_user: User = Depends(get_current_user),
    service: BridgeService = Depends(get_bridge_service),
) -> None:
    revoked = await service.revoke_device(current_user.id, device_id)
    if not revoked:
        raise HTTPException(status_code=404, detail="Device not found")


@router.post("/devices/{device_id}/invoke")
async def invoke_device_tool(
    device_id: str,
    request: InvokeToolRequest,
    current_user: User = Depends(get_current_user),
    service: BridgeService = Depends(get_bridge_service),
) -> dict:
    try:
        return await service.invoke_tool(
            user_id=current_user.id,
            device_id=device_id,
            tool=request.tool,
            args=request.args,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Device not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc