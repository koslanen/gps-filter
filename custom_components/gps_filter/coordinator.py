"""Coordinator for GPS Filter."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


class GPSFilterCoordinator(DataUpdateCoordinator[dict]):
    """GPS Filter coordinator."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
    ) -> None:
        """Initialize coordinator."""

        super().__init__(
            hass,
            _LOGGER,
            name="GPS Filter",
        )

        self.entry = entry
        self.source_entity = entry.data["source"]
        self.data = {}
