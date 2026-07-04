"""GPS Filter device tracker."""

from homeassistant.components.device_tracker import SourceType
from homeassistant.components.device_tracker.config_entry import TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import GPSFilterCoordinator


class FilteredTracker(TrackerEntity):
    """Mirrored GPS tracker."""

    _attr_has_entity_name = True
    _attr_name = "Filtered"

    def __init__(self, coordinator: GPSFilterCoordinator) -> None:
        self.coordinator = coordinator
        self._attr_unique_id = (
            coordinator.entry.entry_id + "_filtered"
        )

    @property
    def latitude(self):
        if self.coordinator.current_point:
            return self.coordinator.current_point.latitude
        return None

    @property
    def longitude(self):
        if self.coordinator.current_point:
            return self.coordinator.current_point.longitude
        return None

    @property
    def location_accuracy(self):
        if self.coordinator.current_point:
            return self.coordinator.current_point.accuracy
        return None

    @property
    def source_type(self):
        return SourceType.GPS

    async def async_added_to_hass(self):
        self.async_on_remove(
            self.coordinator.async_add_listener(
                self.async_write_ha_state
            )
        )


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