import json
from pathlib import Path

from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.core.deps import get_smart_farm_service
from app.services.smart_farm_service import SmartFarmService
from app.smart_farm.schemas import (
    CreateDeviceRequest,
    CreateFarmRequest,
    ExportDatasetRequest,
    GeocodeRequest,
    UpdateFarmRequest,
)
from app.smart_farm.weather_service import geocode_address

router = APIRouter()


@router.get("/schema/{crop_type}")
async def crop_schema(crop_type: str) -> dict:
    path = Path(__file__).resolve().parents[2] / "smart_farm" / "crop_schemas" / f"{crop_type}.json"
    if not path.is_file():
        path = Path(__file__).resolve().parents[2] / "smart_farm" / "crop_schemas" / "japanese_melon.json"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Schema not found")
    return json.loads(path.read_text(encoding="utf-8"))


@router.post("/ingest")
async def ingest_telemetry(
    payload: dict,
    x_device_key: str | None = Header(default=None, alias="X-Device-Key"),
    service: SmartFarmService = Depends(get_smart_farm_service),
) -> dict:
    if not x_device_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="X-Device-Key required")
    try:
        return await service.ingest_device_payload(device_key=x_device_key, payload=payload, source="http")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


@router.get("/farms")
async def list_farms(
    current_user: User = Depends(get_current_user),
    service: SmartFarmService = Depends(get_smart_farm_service),
) -> list[dict]:
    return await service.list_farms(current_user.id)


@router.post("/farms")
async def create_farm(
    request: CreateFarmRequest,
    current_user: User = Depends(get_current_user),
    service: SmartFarmService = Depends(get_smart_farm_service),
) -> dict:
    try:
        return await service.create_farm(current_user.id, request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/farms/{farm_id}")
async def update_farm(
    farm_id: str,
    request: UpdateFarmRequest,
    current_user: User = Depends(get_current_user),
    service: SmartFarmService = Depends(get_smart_farm_service),
) -> dict:
    try:
        return await service.update_farm(current_user.id, farm_id, request)
    except ValueError as exc:
        msg = str(exc)
        code = 404 if "not found" in msg.lower() else 400
        raise HTTPException(status_code=code, detail=msg) from exc


@router.post("/geocode")
async def geocode(
    request: GeocodeRequest,
    current_user: User = Depends(get_current_user),
) -> dict:
    del current_user
    result = await geocode_address(request.address)
    if result is None:
        raise HTTPException(status_code=404, detail="Address not found")
    return result


@router.get("/farms/{farm_id}/weather")
async def farm_weather(
    farm_id: str,
    current_user: User = Depends(get_current_user),
    service: SmartFarmService = Depends(get_smart_farm_service),
) -> dict:
    try:
        return await service.get_farm_weather(current_user.id, farm_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/mqtt-whitelist")
async def mqtt_whitelist(
    current_user: User = Depends(get_current_user),
    service: SmartFarmService = Depends(get_smart_farm_service),
) -> dict:
    del current_user
    return await service.mqtt_whitelist_manifest()


@router.get("/farms/{farm_id}")
async def get_farm(
    farm_id: str,
    current_user: User = Depends(get_current_user),
    service: SmartFarmService = Depends(get_smart_farm_service),
) -> dict:
    detail = await service.get_farm_detail(current_user.id, farm_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Farm not found")
    return detail


@router.post("/farms/{farm_id}/devices")
async def create_device(
    farm_id: str,
    request: CreateDeviceRequest,
    current_user: User = Depends(get_current_user),
    service: SmartFarmService = Depends(get_smart_farm_service),
) -> dict:
    try:
        return await service.create_device(current_user.id, farm_id, request)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/farms/{farm_id}/latest")
async def latest_readings(
    farm_id: str,
    current_user: User = Depends(get_current_user),
    service: SmartFarmService = Depends(get_smart_farm_service),
) -> dict:
    snapshot = await service.latest_snapshot(current_user.id, farm_id)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Farm not found")
    return snapshot


@router.post("/farms/{farm_id}/datasets/export")
async def export_dataset(
    farm_id: str,
    request: ExportDatasetRequest,
    current_user: User = Depends(get_current_user),
    service: SmartFarmService = Depends(get_smart_farm_service),
) -> dict:
    try:
        return await service.export_dataset(current_user.id, farm_id, request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/farms/{farm_id}/upload")
async def upload_dataset_file(
    farm_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    service: SmartFarmService = Depends(get_smart_farm_service),
) -> dict:
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")
    try:
        return await service.import_file(current_user.id, farm_id, file.filename or "upload.csv", content)
    except (ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/datasets/{pack_id}/download")
async def download_dataset(
    pack_id: str,
    current_user: User = Depends(get_current_user),
    service: SmartFarmService = Depends(get_smart_farm_service),
) -> FileResponse:
    result = await service.get_dataset_download(current_user.id, pack_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    path, media_type = result
    return FileResponse(path, media_type=media_type, filename=path.name)