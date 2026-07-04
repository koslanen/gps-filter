"""Diagnostics support for GPS Filter."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .models import FilterResult, GPSPoint


def _redact_config_value(key: str, value: Any) -> Any:
    """Redact sensitive identifiers from config values."""
    if key in {"source", "source_entity"} and isinstance(value, str):
        return "<redacted>"
    return value


def _serialize_gps_point(point: GPSPoint | None) -> dict[str, Any] | None:
    """Serialize a GPS point for diagnostics output."""
    if point is None:
        return None

    return {
        "latitude": point.latitude,
        "longitude": point.longitude,
        "accuracy": point.accuracy,
        "timestamp": point.timestamp.isoformat() if point.timestamp else None,
        "speed": point.speed,
        "course": point.course,
    }


def _serialize_filter_result(result: FilterResult | None) -> dict[str, Any] | None:
    """Serialize a filter result for diagnostics output."""
    if result is None:
        return None

    return {
        "accepted": result.accepted,
        "reason": result.reason,
        "point": _serialize_gps_point(result.point),
        "distance_m": result.distance_m,
        "calculated_speed_kmh": result.calculated_speed_kmh,
        "reported_speed_kmh": result.reported_speed_kmh,
    }


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""

    coordinator = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    data = getattr(coordinator, "data", None)

    manifest_path = Path(__file__).with_name("manifest.json")
    version = None
    if manifest_path.exists():
        with manifest_path.open(encoding="utf-8") as manifest_file:
            version = json.load(manifest_file).get("version")

    configuration = {
        key: _redact_config_value(key, value)
        for key, value in entry.data.items()
    }

    if data is None:
        return {
            "version": version,
            "configuration": configuration,
            "accepted_count": 0,
            "duplicate_count": 0,
            "accuracy_rejections": 0,
            "speed_rejections": 0,
            "last_received_point": None,
            "last_accepted_point": None,
            "last_filter_result": None,
        }

    stats = getattr(data, "engine_stats", None)

    return {
        "version": version,
        "configuration": configuration,
        "accepted_count": getattr(stats, "accepted", 0),
        "duplicate_count": getattr(stats, "duplicate", 0),
        "accuracy_rejections": getattr(stats, "accuracy_rejections", 0),
        "speed_rejections": getattr(stats, "speed_rejections", 0),
        "last_received_point": _serialize_gps_point(data.last_received_point),
        "last_accepted_point": _serialize_gps_point(data.last_accepted_point),
        "last_filter_result": _serialize_filter_result(data.last_result),
    }
