from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ReadingInput(BaseModel):
    channel: str = Field(..., min_length=1, max_length=80)
    value: float | str | bool | None = None
    unit: str = ""
    at: datetime | None = None


class IngestPayload(BaseModel):
    readings: list[ReadingInput] | None = None
    growth_stage: str | None = None
    harvest_cycle_day: int | None = None
    meta: dict[str, Any] = Field(default_factory=dict)


class GatewayIpInput(BaseModel):
    ip: str = Field(..., min_length=7, max_length=45)
    label: str = Field(default="IoT Gateway", max_length=80)


class CreateFarmRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    organization_name: str | None = Field(default=None, max_length=160)
    address: str | None = Field(default=None, max_length=500)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    google_maps_url: str | None = Field(default=None, max_length=500)
    gateway_ips: list[GatewayIpInput] = Field(default_factory=list)
    weather_alerts_enabled: bool = True
    crop_type: str = Field(default="japanese-melon", max_length=80)
    timezone: str = Field(default="Asia/Bangkok", max_length=64)
    auto_export_enabled: bool = True
    auto_export_hours: int = Field(default=24, ge=1, le=168)


class UpdateFarmRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    organization_name: str | None = Field(default=None, max_length=160)
    address: str | None = Field(default=None, max_length=500)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    google_maps_url: str | None = Field(default=None, max_length=500)
    gateway_ips: list[GatewayIpInput] | None = None
    weather_alerts_enabled: bool | None = None
    auto_export_enabled: bool | None = None
    auto_export_hours: int | None = Field(default=None, ge=1, le=168)


class GeocodeRequest(BaseModel):
    address: str = Field(..., min_length=3, max_length=500)


class CreateDeviceRequest(BaseModel):
    device_name: str = Field(..., min_length=1, max_length=120)
    protocol: str = Field(default="http", pattern="^(http|mqtt|csv)$")


class ExportDatasetRequest(BaseModel):
    name: str | None = None
    format: str = Field(default="json", pattern="^(json|csv)$")
    hours: int = Field(default=24, ge=1, le=8760)