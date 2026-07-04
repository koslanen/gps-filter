"""Coordinator for GPS Filter."""

from __future__ import annotations

import logging
from datetime import datetime

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .filter_engine import GPSFilterEngine
from .models import GPSPoint

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

        self.engine = GPSFilterEngine(
            max_speed_kmh=entry.data["max_speed"],
            max_accuracy=entry.data["max_accuracy"],
        )

        self._remove_listener = None

    async def async_start(self) -> None:
        """Start listening for GPS updates."""

        self._remove_listener = async_track_state_change_event(
            self.hass,
            [self.source_entity],
            self._state_changed,
        )

        _LOGGER.info(
            "GPS Filter listening to %s",
            self.source_entity,
        )

    @callback
    def _state_changed(self, event: Event) -> None:
        """Handle tracker updates."""

        state = event.data.get("new_state")

        if state is None:
            return

        latitude = state.attributes.get("latitude")
        longitude = state.attributes.get("longitude")

        if latitude is None or longitude is None:
            return

        accuracy = float(state.attributes.get("gps_accuracy", 9999))
        speed = float(state.attributes.get("speed", 0))

        point = GPSPoint(
            latitude=latitude,
            longitude=longitude,
            accuracy=accuracy,
            timestamp=datetime.now(),
        )

        _LOGGER.info(
            "Received: lat=%.7f lon=%.7f acc=%.1f speed=%.1f",
            latitude,
            longitude,
            accuracy,
            speed,
        )

        result = self.engine.process(point)

        if result.accepted:
            _LOGGER.info(
                "Accepted (%s)",
                result.reason,
            )

            self.data = {
                **state.attributes,
                "speed_kmh": round(speed * 3.6, 1),
            }

            self.async_update_listeners()

        else:
            _LOGGER.info(
                "Rejected (%s)",
                result.reason,
            )

    async def async_stop(self) -> None:
        """Stop listening."""

        if self._remove_listener is not None:
            self._remove_listener()