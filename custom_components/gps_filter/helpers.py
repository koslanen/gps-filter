"""Helpers for GPS Filter."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry


def get_device_name(entry: ConfigEntry) -> str:
    """Return the Home Assistant device name for a config entry."""
    return entry.title or "GPS Filter"
