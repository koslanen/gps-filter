"""Coordinator for GPS Filter."""

from __future__ import annotations

import logging
from collections import deque
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import CONF_MAX_ACCURACY, CONF_MAX_SPEED
from .filter_engine import GPSFilterEngine
from .helpers import get_config_value
from .models import CoordinatorData, FilterResult, FilterTimelineEntry, GPSPoint

_LOGGER = logging.getLogger(__name__)
FILTER_TIMELINE_MAXLEN = 50


def _coerce_float(value: Any, default: float | None = None) -> float | None:
    """Return a float value, or a default when the value cannot be parsed."""
    if value is None:
        return default

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


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
            max_speed=get_config_value(entry, CONF_MAX_SPEED),
            max_accuracy=get_config_value(entry, CONF_MAX_ACCURACY),
        )

        self._remove_listener = None
        self.filter_timeline: deque[FilterTimelineEntry] = deque(
            maxlen=FILTER_TIMELINE_MAXLEN
        )
        self.data = CoordinatorData(engine_stats=self.engine.stats)

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

        latitude = _coerce_float(state.attributes.get("latitude"))
        longitude = _coerce_float(state.attributes.get("longitude"))

        if latitude is None or longitude is None:
            return

        accuracy = _coerce_float(state.attributes.get("gps_accuracy"), 9999.0)
        speed = _coerce_float(state.attributes.get("speed"))

        point = GPSPoint(
            latitude=latitude,
            longitude=longitude,
            accuracy=accuracy,
            timestamp=state.last_updated,
            speed=speed,
        )

        _LOGGER.debug(
            "Received: lat=%.7f lon=%.7f acc=%.1f speed=%s",
            latitude,
            longitude,
            accuracy,
            speed if speed is not None else "unknown",
        )

        result = self.engine.process(point)
        self.filter_timeline.append(
            FilterTimelineEntry(
                timestamp=point.timestamp,
                accepted=result.accepted,
                reason=result.reason,
                latitude=point.latitude,
                longitude=point.longitude,
                accuracy=point.accuracy,
                distance_m=result.distance_m,
                calculated_speed_kmh=result.calculated_speed_kmh,
                reported_speed_kmh=result.reported_speed_kmh,
            )
        )

        new_data = CoordinatorData(
            last_received_point=point,
            last_accepted_point=point if result.accepted else self.last_accepted_point,
            last_result=result,
            engine_stats=self.engine.stats,
        )

        self.async_set_updated_data(new_data)

        if result.accepted:
            _LOGGER.debug(
                "Accepted point:\n"
                "- reason: %s\n"
                "- distance: %s m\n"
                "- calculated speed: %s km/h\n"
                "- reported speed: %s km/h\n"
                "- accuracy: %.1f",
                result.reason,
                result.distance_m,
                result.calculated_speed_kmh,
                result.reported_speed_kmh,
                accuracy,
            )
        else:
            _LOGGER.debug(
                "Rejected point:\n"
                "- reason: %s\n"
                "- distance: %s m\n"
                "- calculated speed: %s km/h\n"
                "- reported speed: %s km/h\n"
                "- accuracy: %.1f",
                result.reason,
                result.distance_m,
                result.calculated_speed_kmh,
                result.reported_speed_kmh,
                accuracy,
            )

    def reset_statistics(self) -> None:
        """Reset filter statistics."""
        _LOGGER.info(
            "Resetting GPS Filter statistics for %s",
            self.source_entity,
        )
        self.engine.stats = type(self.engine.stats)()
        self.async_set_updated_data(
            CoordinatorData(
                last_received_point=self.last_received_point,
                last_accepted_point=self.last_accepted_point,
                last_result=self.last_result,
                engine_stats=self.engine.stats,
            )
        )

    def reset_filter(self) -> None:
        """Reset the filter engine state and statistics."""
        _LOGGER.info(
            "Resetting GPS Filter state for %s",
            self.source_entity,
        )
        self.engine = GPSFilterEngine(
            max_speed=get_config_value(self.entry, CONF_MAX_SPEED),
            max_accuracy=get_config_value(self.entry, CONF_MAX_ACCURACY),
        )
        self.filter_timeline.clear()
        self.async_set_updated_data(CoordinatorData(engine_stats=self.engine.stats))

    async def async_stop(self) -> None:
        """Stop listening."""

        if self._remove_listener is not None:
            self._remove_listener()
            self._remove_listener = None
