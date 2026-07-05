"""GPS Filter device tracker."""

from homeassistant.components.device_tracker import SourceType, TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import GPSFilterCoordinator
from .helpers import get_device_name


class FilteredTracker(CoordinatorEntity[GPSFilterCoordinator], TrackerEntity):
    """Mirrored GPS tracker."""

    _attr_has_entity_name = True
    _attr_name = "Filtered"

    def __init__(self, coordinator: GPSFilterCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = coordinator.entry.entry_id + "_filtered"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.entry.entry_id)},
            "name": get_device_name(coordinator.entry),
            "manufacturer": "GPS Filter",
            "model": "Filtered Tracker",
        }

    @property
    def latitude(self):
        if self.coordinator.last_accepted_point:
            return self.coordinator.last_accepted_point.latitude
        return None

    @property
    def longitude(self):
        if self.coordinator.last_accepted_point:
            return self.coordinator.last_accepted_point.longitude
        return None

    @property
    def location_accuracy(self):
        if self.coordinator.last_accepted_point:
            return self.coordinator.last_accepted_point.accuracy
        return None

    @property
    def source_type(self):
        return SourceType.GPS

    @property
    def extra_state_attributes(self):
        attributes = {}

        stats = self.coordinator.data.engine_stats
        attributes["accepted_count"] = stats.accepted
        attributes["duplicate_count"] = stats.duplicate
        attributes["accuracy_rejections"] = stats.accuracy_rejections
        attributes["startup_accuracy_rejections"] = (
            stats.startup_accuracy_rejections
        )
        attributes["speed_rejections"] = stats.speed_rejections
        attributes["speed_consistency_rejections"] = (
            stats.speed_consistency_rejections
        )
        attributes["gap_accepted_count"] = stats.gap_accepted

        attributes["last_received_accuracy"] = None
        attributes["last_received_timestamp"] = None
        attributes["last_result_reason"] = None
        attributes["last_result_accepted"] = None
        attributes["last_distance_m"] = None
        attributes["last_calculated_speed_kmh"] = None
        attributes["last_reported_speed_kmh"] = None
        attributes["last_seconds_since_accepted"] = None

        if self.coordinator.last_received_point is not None:
            attributes["last_received_accuracy"] = (
                self.coordinator.last_received_point.accuracy
            )
            attributes["last_received_timestamp"] = (
                self.coordinator.last_received_point.timestamp.isoformat()
            )

        if self.coordinator.last_accepted_point is not None:
            attributes["last_accepted_accuracy"] = (
                self.coordinator.last_accepted_point.accuracy
            )

        if self.coordinator.last_result is not None:
            attributes["last_result_reason"] = self.coordinator.last_result.reason
            attributes["last_result_accepted"] = getattr(
                self.coordinator.last_result,
                "accepted",
                None,
            )
            attributes["last_distance_m"] = self.coordinator.last_result.distance_m
            attributes["last_calculated_speed_kmh"] = (
                self.coordinator.last_result.calculated_speed_kmh
            )
            attributes["last_reported_speed_kmh"] = (
                self.coordinator.last_result.reported_speed_kmh
            )
            attributes["last_seconds_since_accepted"] = (
                getattr(
                    self.coordinator.last_result,
                    "seconds_since_last_accepted",
                    None,
                )
            )

        return attributes

    async def async_added_to_hass(self):
        await super().async_added_to_hass()


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    coordinator: GPSFilterCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [
            FilteredTracker(coordinator),
        ]
    )
