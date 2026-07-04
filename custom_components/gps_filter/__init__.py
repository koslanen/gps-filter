"""GPS Filter."""

from __future__ import annotations

import logging

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall, callback

from .const import DOMAIN, PLATFORMS
from .coordinator import GPSFilterCoordinator

_LOGGER = logging.getLogger(__name__)
SERVICE_FIELD_ENTRY_ID = "entry_id"
RESET_SERVICE_SCHEMA = vol.Schema({vol.Optional(SERVICE_FIELD_ENTRY_ID): str})


@callback
def _async_handle_reset_statistics(call: ServiceCall) -> None:
    """Reset filter statistics for all entries."""
    _LOGGER.info("Resetting GPS Filter statistics")
    for coordinator in _iter_coordinators(
        call.hass,
        call.data.get(SERVICE_FIELD_ENTRY_ID),
    ):
        coordinator.reset_statistics()


@callback
def _async_handle_reset_filter(call: ServiceCall) -> None:
    """Reset filter state and statistics for all entries."""
    _LOGGER.info("Resetting GPS Filter state")
    for coordinator in _iter_coordinators(
        call.hass,
        call.data.get(SERVICE_FIELD_ENTRY_ID),
    ):
        coordinator.reset_filter()


@callback
def _iter_coordinators(
    hass: HomeAssistant,
    entry_id: str | None = None,
) -> list[GPSFilterCoordinator]:
    """Return all loaded GPS Filter coordinators."""
    return [
        coordinator
        for loaded_entry_id, coordinator in hass.data.get(DOMAIN, {}).items()
        if isinstance(coordinator, GPSFilterCoordinator)
        and (entry_id is None or loaded_entry_id == entry_id)
    ]


async def async_setup(
    hass: HomeAssistant,
    config: dict,
) -> bool:
    """Set up GPS Filter."""
    hass.data.setdefault(DOMAIN, {})

    hass.services.async_register(
        DOMAIN,
        "reset_statistics",
        _async_handle_reset_statistics,
        schema=RESET_SERVICE_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        "reset_filter",
        _async_handle_reset_filter,
        schema=RESET_SERVICE_SCHEMA,
    )

    return True


async def _async_update_listener(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> None:
    """Handle options updates."""
    _LOGGER.info("Reloading GPS Filter after options update")
    await hass.config_entries.async_reload(entry.entry_id)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Set up a GPS Filter config entry."""

    coordinator = GPSFilterCoordinator(
        hass,
        entry,
    )

    await coordinator.async_start()

    hass.data[DOMAIN][entry.entry_id] = coordinator
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    await hass.config_entries.async_forward_entry_setups(
        entry,
        PLATFORMS,
    )

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Unload a GPS Filter config entry."""

    unload_ok = await hass.config_entries.async_unload_platforms(
        entry,
        PLATFORMS,
    )

    if unload_ok:
        coordinator: GPSFilterCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.async_stop()
        _LOGGER.info("Unloaded GPS Filter for %s", coordinator.source_entity)

    if not hass.data[DOMAIN]:
        hass.services.async_remove(DOMAIN, "reset_statistics")
        hass.services.async_remove(DOMAIN, "reset_filter")

    return unload_ok
