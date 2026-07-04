"""Helpers for GPS Filter."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry

from .const import (
    CONF_MAX_ACCURACY,
    CONF_MAX_SPEED,
    DEFAULT_MAX_ACCURACY,
    DEFAULT_MAX_SPEED,
)


def get_device_name(entry: ConfigEntry) -> str:
    """Return the Home Assistant device name for a config entry."""
    return entry.title or "GPS Filter"


def get_config_value(entry: ConfigEntry, key: str):
    """Return an option value, falling back to config entry data."""
    return getattr(entry, "options", {}).get(key, entry.data[key])


def get_effective_filter_config(entry: ConfigEntry) -> dict[str, float]:
    """Return the effective filter threshold configuration."""
    return {
        CONF_MAX_SPEED: getattr(entry, "options", {}).get(
            CONF_MAX_SPEED,
            entry.data.get(CONF_MAX_SPEED, DEFAULT_MAX_SPEED),
        ),
        CONF_MAX_ACCURACY: getattr(entry, "options", {}).get(
            CONF_MAX_ACCURACY,
            entry.data.get(CONF_MAX_ACCURACY, DEFAULT_MAX_ACCURACY),
        ),
    }
