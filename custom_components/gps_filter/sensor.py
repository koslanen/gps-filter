"""Sensor platform for GPS Filter."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfLength, UnitOfSpeed
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import GPSFilterCoordinator
from .helpers import get_device_name


@dataclass(frozen=True, kw_only=True)
class GPSFilterSensorEntityDescription(SensorEntityDescription):
    """Describe a GPS Filter sensor."""

    value_fn: Callable[[GPSFilterCoordinator], Any]


def _status_value(coordinator: GPSFilterCoordinator) -> str:
    """Return the current filter decision state."""
    result = coordinator.last_result
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


def _last_received_timestamp(coordinator: GPSFilterCoordinator):
    """Return the last received point timestamp."""
    if coordinator.last_received_point is None:
        return None
    return coordinator.last_received_point.timestamp


def _last_accepted_timestamp(coordinator: GPSFilterCoordinator):
    """Return the last accepted point timestamp."""
    if coordinator.last_accepted_point is None:
        return None
    return coordinator.last_accepted_point.timestamp


SENSOR_DESCRIPTIONS: tuple[GPSFilterSensorEntityDescription, ...] = (
    GPSFilterSensorEntityDescription(
        key="status",
        translation_key="status",
        icon="mdi:filter-check",
        value_fn=_status_value,
    ),
    GPSFilterSensorEntityDescription(
        key="distance",
        translation_key="distance",
        icon="mdi:ruler",
        native_unit_of_measurement=UnitOfLength.METERS,
        device_class=SensorDeviceClass.DISTANCE,
        value_fn=lambda coordinator: (
            0.0
            if coordinator.last_result is None
            or coordinator.last_result.distance_m is None
            else coordinator.last_result.distance_m
        ),
    ),
    GPSFilterSensorEntityDescription(
        key="calculated_speed",
        translation_key="calculated_speed",
        icon="mdi:speedometer",
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        device_class=SensorDeviceClass.SPEED,
        value_fn=lambda coordinator: (
            0.0
            if coordinator.last_result is None
            or coordinator.last_result.calculated_speed_kmh is None
            else coordinator.last_result.calculated_speed_kmh
        ),
    ),
    GPSFilterSensorEntityDescription(
        key="reported_speed",
        translation_key="reported_speed",
        icon="mdi:speedometer",
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        device_class=SensorDeviceClass.SPEED,
        value_fn=lambda coordinator: (
            0.0
            if coordinator.last_result is None
            or coordinator.last_result.reported_speed_kmh is None
            else coordinator.last_result.reported_speed_kmh
        ),
    ),
    GPSFilterSensorEntityDescription(
        key="last_reason",
        translation_key="last_reason",
        icon="mdi:information-outline",
        value_fn=lambda coordinator: (
            "unknown"
            if coordinator.last_result is None
            else coordinator.last_result.reason or "unknown"
        ),
    ),
    GPSFilterSensorEntityDescription(
        key="last_accuracy",
        translation_key="last_accuracy",
        icon="mdi:crosshairs-gps",
        native_unit_of_measurement=UnitOfLength.METERS,
        device_class=SensorDeviceClass.DISTANCE,
        value_fn=lambda coordinator: (
            0.0
            if coordinator.last_received_point is None
            else coordinator.last_received_point.accuracy
        ),
    ),
    GPSFilterSensorEntityDescription(
        key="last_received_timestamp",
        translation_key="last_received_timestamp",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=_last_received_timestamp,
    ),
    GPSFilterSensorEntityDescription(
        key="last_accepted_timestamp",
        translation_key="last_accepted_timestamp",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=_last_accepted_timestamp,
    ),
    GPSFilterSensorEntityDescription(
        key="acceptance_rate",
        translation_key="acceptance_rate",
        icon="mdi:percent-outline",
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda coordinator: coordinator.acceptance_rate_percent,
    ),
    GPSFilterSensorEntityDescription(
        key="max_distance",
        translation_key="max_distance",
        icon="mdi:map-marker-distance",
        native_unit_of_measurement=UnitOfLength.METERS,
        device_class=SensorDeviceClass.DISTANCE,
        value_fn=lambda coordinator: coordinator.summary_stats.max_distance_m,
    ),
    GPSFilterSensorEntityDescription(
        key="max_calculated_speed",
        translation_key="max_calculated_speed",
        icon="mdi:speedometer",
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        device_class=SensorDeviceClass.SPEED,
        value_fn=lambda coordinator: (
            coordinator.summary_stats.max_calculated_speed_kmh
        ),
    ),
    GPSFilterSensorEntityDescription(
        key="max_reported_speed",
        translation_key="max_reported_speed",
        icon="mdi:speedometer",
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        device_class=SensorDeviceClass.SPEED,
        value_fn=lambda coordinator: coordinator.summary_stats.max_reported_speed_kmh,
    ),
    GPSFilterSensorEntityDescription(
        key="max_accuracy",
        translation_key="max_accuracy",
        icon="mdi:crosshairs-gps",
        native_unit_of_measurement=UnitOfLength.METERS,
        device_class=SensorDeviceClass.DISTANCE,
        value_fn=lambda coordinator: coordinator.summary_stats.max_accuracy_m,
    ),
    GPSFilterSensorEntityDescription(
        key="accepted_count",
        translation_key="accepted_count",
        icon="mdi:check-circle-outline",
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda coordinator: coordinator.data.engine_stats.accepted,
    ),
    GPSFilterSensorEntityDescription(
        key="duplicate_count",
        translation_key="duplicate_count",
        icon="mdi:content-duplicate",
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda coordinator: coordinator.data.engine_stats.duplicate,
    ),
    GPSFilterSensorEntityDescription(
        key="accuracy_rejections",
        translation_key="accuracy_rejections",
        icon="mdi:alert-circle-outline",
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda coordinator: coordinator.data.engine_stats.accuracy_rejections,
    ),
    GPSFilterSensorEntityDescription(
        key="speed_rejections",
        translation_key="speed_rejections",
        icon="mdi:alert-outline",
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda coordinator: coordinator.data.engine_stats.speed_rejections,
    ),
)


class GPSFilterSensor(CoordinatorEntity[GPSFilterCoordinator], SensorEntity):
    """GPS Filter diagnostic sensor."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_entity_registry_enabled_default = True

    entity_description: GPSFilterSensorEntityDescription

    def __init__(
        self,
        coordinator: GPSFilterCoordinator,
        description: GPSFilterSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.entry.entry_id)},
            "name": get_device_name(coordinator.entry),
            "manufacturer": "GPS Filter",
            "model": "Filtered Tracker",
        }

    @property
    def native_value(self) -> Any:
        """Return the sensor value."""
        return self.entity_description.value_fn(self.coordinator)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up GPS Filter sensors."""
    coordinator: GPSFilterCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [
            GPSFilterSensor(coordinator, description)
            for description in SENSOR_DESCRIPTIONS
        ]
    )
