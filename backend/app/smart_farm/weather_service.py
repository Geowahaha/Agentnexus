"""Open-Meteo forecast + greenhouse risk alerts (no API key required)."""

from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

OPEN_METEO = "https://api.open-meteo.com/v1/forecast"
NOMINATIM = "https://nominatim.openstreetmap.org/search"

# WMO weather codes: https://open-meteo.com/en/docs
_THUNDERSTORM = frozenset(range(95, 100))
_HEAVY_RAIN = frozenset({65, 82})
_RAIN = frozenset({51, 53, 55, 61, 63, 65, 80, 81, 82})


def _risk_level(code: int, precip_mm: float, wind_kmh: float) -> str | None:
    if code in _THUNDERSTORM:
        return "critical"
    if code in _HEAVY_RAIN or precip_mm >= 25:
        return "high"
    if code in _RAIN or precip_mm >= 10:
        return "medium"
    if wind_kmh >= 54:
        return "high"
    if wind_kmh >= 40:
        return "medium"
    return None


def _alert_message(code: int, precip_mm: float, wind_kmh: float, level: str) -> str:
    if code in _THUNDERSTORM:
        return "พายุฝนฟ้าคะนอง — ปิดระบบระบายน้ำ ตรวจโรงเรือนและผ้าคลุมทันที"
    if precip_mm >= 25 or code in _HEAVY_RAIN:
        return f"ฝนตกหนักคาด ~{precip_mm:.0f} mm — เตรียมรับมือน้ำท่วมขังและความชื้นสูง"
    if code in _RAIN or precip_mm >= 10:
        return f"มีฝนคาด ~{precip_mm:.0f} mm — ลดการให้น้ำ ตรวจ drainage"
    if wind_kmh >= 40:
        return f"ลมแรง ~{wind_kmh:.0f} km/h — ตรวจโครงโรงเรือนและผ้าร่ม"
    return "สภาพอากาศควรเฝ้าระวัง"


async def geocode_address(address: str) -> dict[str, Any] | None:
    query = address.strip()
    if not query:
        return None
    headers = {"User-Agent": "OBOLLA-SmartFarm/1.0 (obolla.com)"}
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(
            NOMINATIM,
            params={"q": query, "format": "json", "limit": 1},
            headers=headers,
        )
        resp.raise_for_status()
        rows = resp.json()
    if not rows:
        return None
    hit = rows[0]
    lat = float(hit["lat"])
    lon = float(hit["lon"])
    return {
        "latitude": lat,
        "longitude": lon,
        "display_name": hit.get("display_name", query),
        "google_maps_url": f"https://www.google.com/maps/search/?api=1&query={lat},{lon}",
        "openstreetmap_url": f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map=15/{lat}/{lon}",
    }


async def fetch_weather(latitude: float, longitude: float, *, timezone: str = "Asia/Bangkok") -> dict[str, Any]:
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "timezone": timezone,
        "current": "temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m",
        "daily": "weather_code,precipitation_sum,wind_speed_10m_max",
        "forecast_days": 5,
    }
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.get(OPEN_METEO, params=params)
        resp.raise_for_status()
        data = resp.json()
    current = data.get("current") or {}
    daily = data.get("daily") or {}
    return {
        "source": "open-meteo",
        "latitude": latitude,
        "longitude": longitude,
        "current": {
            "temperature_c": current.get("temperature_2m"),
            "humidity_pct": current.get("relative_humidity_2m"),
            "precipitation_mm": current.get("precipitation"),
            "wind_speed_kmh": current.get("wind_speed_10m"),
            "weather_code": current.get("weather_code"),
        },
        "daily": [
            {
                "date": daily.get("time", [None])[i],
                "weather_code": (daily.get("weather_code") or [None])[i],
                "precipitation_sum_mm": (daily.get("precipitation_sum") or [0])[i],
                "wind_max_kmh": (daily.get("wind_speed_10m_max") or [0])[i],
            }
            for i in range(min(5, len(daily.get("time") or [])))
        ],
    }


def should_stop_irrigation(weather: dict[str, Any], threshold_mm: float = 5.0) -> bool:
    """Return True if rain forecast suggests skipping irrigation."""
    current = weather.get("current") or {}
    precip = float(current.get("precipitation_mm") or 0)
    if precip >= threshold_mm:
        return True
    for day in weather.get("daily") or []:
        if float(day.get("precipitation_sum_mm") or 0) >= threshold_mm:
            return True
    return False

def build_weather_alerts(weather: dict[str, Any]) -> list[dict[str, Any]]:
    alerts: list[dict[str, Any]] = []
    current = weather.get("current") or {}
    code = int(current.get("weather_code") or 0)
    precip = float(current.get("precipitation_mm") or 0)
    wind = float(current.get("wind_speed_kmh") or 0)
    level = _risk_level(code, precip, wind)
    if level:
        alerts.append(
            {
                "level": level,
                "type": "current",
                "message": _alert_message(code, precip, wind, level),
                "weather_code": code,
                "precipitation_mm": precip,
                "wind_speed_kmh": wind,
            }
        )
    for day in weather.get("daily") or []:
        d_code = int(day.get("weather_code") or 0)
        d_precip = float(day.get("precipitation_sum_mm") or 0)
        d_wind = float(day.get("wind_max_kmh") or 0)
        d_level = _risk_level(d_code, d_precip, d_wind)
        if d_level in ("medium", "high", "critical"):
            alerts.append(
                {
                    "level": d_level,
                    "type": "forecast",
                    "date": day.get("date"),
                    "message": _alert_message(d_code, d_precip, d_wind, d_level),
                    "weather_code": d_code,
                    "precipitation_sum_mm": d_precip,
                    "wind_max_kmh": d_wind,
                }
            )
    order = {"critical": 0, "high": 1, "medium": 2}
    alerts.sort(key=lambda a: order.get(a["level"], 9))
    return alerts