"""Sensor platform for GPS Filter."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfLength, UnitOfSpeed
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import GPSFilterCoordinator


class GPSFilterSensor(CoordinatorEntity[GPSFilterCoordinator], SensorEntity):
    """Base class for GPS Filter sensors."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_entity_registry_enabled_default = True
    translation_key: str | None = None

    def __init__(self, coordinator: GPSFilterCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{self.entity_key}"
        self._attr_translation_key = self.translation_key
        self._attr_name = None
        self._attr_entity_id = f"sensor.gps_filter_{self.entity_key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.entry.entry_id)},
            "name": "GPS Filter",
            "manufacturer": "GPS Filter",
            "model": "Filtered Tracker",
        }

    @property
    def entity_description_key(self) -> str:
        """Return the entity key for naming."""
        return self.entity_key


class GPSFilterStatusSensor(GPSFilterSensor):
    """Expose the latest filter decision state."""

    entity_key = "status"
    translation_key = "status"
    _attr_icon = "mdi:filter-check"

    @property
    def native_value(self) -> str:
        """Return the current filter decision state."""
        result = self.coordinator.last_result
        if result is None:
            return "unknown"
        if result.reason == "first_point":
            return "first_point"
        if result.accepted:
            return "accepted"
        if result.reason == "duplicate":
            return "duplicate"
        if result.reason == "accuracy":
            return "accuracy"
        if result.reason == "speed":
            return "speed"
        return result.reason


class GPSFilterCalculatedSpeedSensor(GPSFilterSensor):
    """Expose the calculated speed from the last accepted point."""

    entity_key = "calculated_speed"
    translation_key = "calculated_speed"
    _attr_icon = "mdi:speedometer"
    _attr_native_unit_of_measurement = UnitOfSpeed.KILOMETERS_PER_HOUR
    _attr_device_class = SensorDeviceClass.SPEED
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> float:
        """Return the calculated speed."""
        result = self.coordinator.last_result
        if result is None or result.calculated_speed_kmh is None:
            return 0.0
        return result.calculated_speed_kmh


class GPSFilterReportedSpeedSensor(GPSFilterSensor):
    """Expose the reported speed from the last processed point."""

    entity_key = "reported_speed"
    translation_key = "reported_speed"
    _attr_icon = "mdi:speedometer"
    _attr_native_unit_of_measurement = UnitOfSpeed.KILOMETERS_PER_HOUR
    _attr_device_class = SensorDeviceClass.SPEED
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> float:
        """Return the reported speed."""
        result = self.coordinator.last_result
        if result is None or result.reported_speed_kmh is None:
            return 0.0
        return result.reported_speed_kmh


class GPSFilterDistanceSensor(GPSFilterSensor):
    """Expose the distance from the last processed point."""

    entity_key = "distance"
    translation_key = "distance"
    _attr_icon = "mdi:ruler"
    _attr_native_unit_of_measurement = UnitOfLength.METERS
    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> float:
        """Return the distance."""
        result = self.coordinator.last_result
        if result is None or result.distance_m is None:
            return 0.0
        return result.distance_m


class GPSFilterLastReasonSensor(GPSFilterSensor):
    """Expose the last filter reason."""

    entity_key = "last_reason"
    translation_key = "last_reason"
    _attr_icon = "mdi:information-outline"

    @property
    def native_value(self) -> str:
        """Return the last filter reason."""
        result = self.coordinator.last_result
        if result is None:
            return "unknown"
        return result.reason or "unknown"


class GPSFilterLastAccuracySensor(GPSFilterSensor):
    """Expose the last received accuracy."""

    entity_key = "last_accuracy"
    translation_key = "last_accuracy"
    _attr_icon = "mdi:crosshairs-gps"
    _attr_native_unit_of_measurement = UnitOfLength.METERS
    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> float:
        """Return the last received accuracy."""
        if self.coordinator.last_received_point is None:
            return 0.0
        return self.coordinator.last_received_point.accuracy


class GPSFilterAcceptedCountSensor(GPSFilterSensor):
    """Expose the number of accepted points."""

    entity_key = "accepted_count"
    translation_key = "accepted_count"
    _attr_icon = "mdi:check-circle-outline"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    @property
    def native_value(self) -> int:
        """Return the accepted count."""
        return self.coordinator.data.engine_stats.accepted


class GPSFilterDuplicateCountSensor(GPSFilterSensor):
    """Expose the number of duplicate points."""

    entity_key = "duplicate_count"
    translation_key = "duplicate_count"
    _attr_icon = "mdi:content-duplicate"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    @property
    def native_value(self) -> int:
        """Return the duplicate count."""
        return self.coordinator.data.engine_stats.duplicate


class GPSFilterAccuracyRejectionsSensor(GPSFilterSensor):
    """Expose the number of accuracy rejections."""

    entity_key = "accuracy_rejections"
    translation_key = "accuracy_rejections"
    _attr_icon = "mdi:alert-circle-outline"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    @property
    def native_value(self) -> int:
        """Return the accuracy rejection count."""
        return self.coordinator.data.engine_stats.accuracy_rejections


class GPSFilterSpeedRejectionsSensor(GPSFilterSensor):
    """Expose the number of speed rejections."""

    entity_key = "speed_rejections"
    translation_key = "speed_rejections"
    _attr_icon = "mdi:alert-outline"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    @property
    def native_value(self) -> int:
        """Return the speed rejection count."""
        return self.coordinator.data.engine_stats.speed_rejections


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up GPS Filter sensors."""
    coordinator: GPSFilterCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        GPSFilterStatusSensor(coordinator),
        GPSFilterCalculatedSpeedSensor(coordinator),
        GPSFilterReportedSpeedSensor(coordinator),
        GPSFilterDistanceSensor(coordinator),
        GPSFilterLastReasonSensor(coordinator),
        GPSFilterLastAccuracySensor(coordinator),
        GPSFilterAcceptedCountSensor(coordinator),
        GPSFilterDuplicateCountSensor(coordinator),
        GPSFilterAccuracyRejectionsSensor(coordinator),
        GPSFilterSpeedRejectionsSensor(coordinator),
    ]

    async_add_entities(entities)
