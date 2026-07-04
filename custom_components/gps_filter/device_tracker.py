"""GPS Filter device tracker."""

from homeassistant.components.device_tracker import SourceType
from homeassistant.components.device_tracker.config_entry import TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import GPSFilterCoordinator


class FilteredTracker(CoordinatorEntity[GPSFilterCoordinator], TrackerEntity):
    """Mirrored GPS tracker."""

    _attr_has_entity_name = True
    _attr_name = "Filtered"

    def __init__(self, coordinator: GPSFilterCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = coordinator.entry.entry_id + "_filtered"

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
