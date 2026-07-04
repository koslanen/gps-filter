"""Diagnostics support for GPS Filter."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, VERSION
from .helpers import get_effective_filter_config
from .models import FilterResult, FilterTimelineEntry, GPSPoint


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


def _serialize_timeline_entry(entry: FilterTimelineEntry) -> dict[str, Any]:
    """Serialize a filter timeline entry for diagnostics output."""
    return {
        "timestamp": entry.timestamp.isoformat(),
        "accepted": entry.accepted,
        "reason": entry.reason,
        "latitude": entry.latitude,
        "longitude": entry.longitude,
        "accuracy": entry.accuracy,
        "distance_m": entry.distance_m,
        "calculated_speed_kmh": entry.calculated_speed_kmh,
        "reported_speed_kmh": entry.reported_speed_kmh,
    }


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""

    coordinator = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    data = getattr(coordinator, "data", None)
    filter_timeline = [
        _serialize_timeline_entry(timeline_entry)
        for timeline_entry in getattr(coordinator, "filter_timeline", ())
    ]

    configuration = {
        key: _redact_config_value(key, value)
        for key, value in entry.data.items()
    }
    effective_filter_config = get_effective_filter_config(entry)

    if data is None:
        return {
            "version": VERSION,
            "configuration": configuration,
            "effective_filter_config": effective_filter_config,
            "accepted_count": 0,
            "duplicate_count": 0,
            "accuracy_rejections": 0,
            "speed_rejections": 0,
            "last_received_point": None,
            "last_accepted_point": None,
            "last_filter_result": None,
            "filter_timeline": filter_timeline,
        }

    stats = getattr(data, "engine_stats", None)

    return {
        "version": VERSION,
        "configuration": configuration,
        "effective_filter_config": effective_filter_config,
        "accepted_count": getattr(stats, "accepted", 0),
        "duplicate_count": getattr(stats, "duplicate", 0),
        "accuracy_rejections": getattr(stats, "accuracy_rejections", 0),
        "speed_rejections": getattr(stats, "speed_rejections", 0),
        "last_received_point": _serialize_gps_point(data.last_received_point),
        "last_accepted_point": _serialize_gps_point(data.last_accepted_point),
        "last_filter_result": _serialize_filter_result(data.last_result),
        "filter_timeline": filter_timeline,
    }
