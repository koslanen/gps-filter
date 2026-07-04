"""Button platform for GPS Filter."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import GPSFilterCoordinator
from .helpers import get_device_name


@dataclass(frozen=True, kw_only=True)
class GPSFilterButtonEntityDescription(ButtonEntityDescription):
    """Describe a GPS Filter button."""

    press_fn: Callable[[GPSFilterCoordinator], None]


BUTTON_DESCRIPTIONS: tuple[GPSFilterButtonEntityDescription, ...] = (
    GPSFilterButtonEntityDescription(
        key="reset_filter",
        translation_key="reset_filter",
        icon="mdi:restart",
        press_fn=lambda coordinator: coordinator.reset_filter(),
    ),
    GPSFilterButtonEntityDescription(
        key="reset_statistics",
        translation_key="reset_statistics",
        icon="mdi:counter",
        press_fn=lambda coordinator: coordinator.reset_statistics(),
    ),
)


class GPSFilterButton(CoordinatorEntity[GPSFilterCoordinator], ButtonEntity):
    """GPS Filter reset button."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    entity_description: GPSFilterButtonEntityDescription

    def __init__(
        self,
        coordinator: GPSFilterCoordinator,
        description: GPSFilterButtonEntityDescription,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.entry.entry_id)},
            "name": get_device_name(coordinator.entry),
            "manufacturer": "GPS Filter",
            "model": "Filtered Tracker",
        }

    async def async_press(self) -> None:
        """Press the button."""
        self.entity_description.press_fn(self.coordinator)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up GPS Filter buttons."""
    coordinator: GPSFilterCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [
            GPSFilterButton(coordinator, description)
            for description in BUTTON_DESCRIPTIONS
        ]
    )
