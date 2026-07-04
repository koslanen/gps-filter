"""Coordinator for GPS Filter."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .filter_engine import GPSFilterEngine
from .models import CoordinatorData, FilterResult, GPSPoint

_LOGGER = logging.getLogger(__name__)


class GPSFilterCoordinator(DataUpdateCoordinator[CoordinatorData]):
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
            max_speed=entry.data["max_speed"],
            max_accuracy=entry.data["max_accuracy"],
        )

        self._remove_listener = None
        self.data = CoordinatorData()

    @property
    def current_point(self) -> GPSPoint | None:
        """Return the last accepted point."""

        return self.last_accepted_point

    @property
    def last_received_point(self) -> GPSPoint | None:
        """Return the most recently received point."""

        return self.data.last_received_point

    @property
    def last_accepted_point(self) -> GPSPoint | None:
        """Return the most recently accepted point."""

        return self.data.last_accepted_point

    @property
    def last_result(self) -> FilterResult | None:
        """Return the most recent filter result."""

        return self.data.last_result

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
            timestamp=state.last_updated,
        )

        _LOGGER.info(
            "Received: lat=%.7f lon=%.7f acc=%.1f speed=%.1f",
            latitude,
            longitude,
            accuracy,
            speed,
        )

        result = self.engine.process(point)

        new_data = CoordinatorData(
            last_received_point=point,
            last_accepted_point=point if result.accepted else self.last_accepted_point,
            last_result=result,
        )

        self.async_set_updated_data(new_data)

        if result.accepted:
            _LOGGER.info(
                "Accepted (%s)",
                result.reason,
            )
        else:
            _LOGGER.info(
                "Rejected (%s)",
                result.reason,
            )

    async def async_stop(self) -> None:
        """Stop listening."""

        if self._remove_listener is not None:
            self._remove_listener()
