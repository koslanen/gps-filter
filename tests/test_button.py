import asyncio
from unittest.mock import Mock

import homeassistant.helpers.frame as frame
import pytest

from custom_components.gps_filter.button import BUTTON_DESCRIPTIONS, GPSFilterButton
from custom_components.gps_filter.coordinator import GPSFilterCoordinator


class DummyEntry:
    def __init__(self) -> None:
        self.entry_id = "entry-1"
        self.title = "GPS Filter - Test Tracker"
        self.data = {
            "source": "device_tracker.test",
            "max_speed": 220.0,
            "max_accuracy": 30.0,
        }
        self.options = {}


@pytest.fixture(autouse=True)
def _disable_frame_reporting(monkeypatch):
    monkeypatch.setattr(frame, "report_usage", lambda *args, **kwargs: None)


def _make_buttons(coordinator):
    return {
        description.key: GPSFilterButton(coordinator, description)
        for description in BUTTON_DESCRIPTIONS
    }


def test_button_entities_follow_home_assistant_entity_conventions():
    coordinator = GPSFilterCoordinator(hass=Mock(), entry=DummyEntry())
    buttons = _make_buttons(coordinator)

    assert list(buttons) == ["reset_filter", "reset_statistics"]
    translation_keys = [
        button.entity_description.translation_key for button in buttons.values()
    ]
    assert translation_keys == [
        "reset_filter",
        "reset_statistics",
    ]
    assert [button.unique_id for button in buttons.values()] == [
        "entry-1_reset_filter",
        "entry-1_reset_statistics",
    ]
    assert all(button.has_entity_name for button in buttons.values())


def test_button_entities_share_gps_filter_device_info():
    coordinator = GPSFilterCoordinator(hass=Mock(), entry=DummyEntry())
    button = GPSFilterButton(coordinator, BUTTON_DESCRIPTIONS[0])

    assert button.device_info == {
        "identifiers": {("gps_filter", "entry-1")},
        "name": "GPS Filter - Test Tracker",
        "manufacturer": "GPS Filter",
        "model": "Filtered Tracker",
    }


def test_reset_filter_button_only_calls_own_coordinator():
    coordinator = GPSFilterCoordinator(hass=Mock(), entry=DummyEntry())
    coordinator.reset_filter = Mock()
    coordinator.reset_statistics = Mock()
    buttons = _make_buttons(coordinator)

    asyncio.run(buttons["reset_filter"].async_press())

    coordinator.reset_filter.assert_called_once()
    coordinator.reset_statistics.assert_not_called()


def test_reset_statistics_button_only_calls_own_coordinator():
    coordinator = GPSFilterCoordinator(hass=Mock(), entry=DummyEntry())
    coordinator.reset_filter = Mock()
    coordinator.reset_statistics = Mock()
    buttons = _make_buttons(coordinator)

    asyncio.run(buttons["reset_statistics"].async_press())

    coordinator.reset_filter.assert_not_called()
    coordinator.reset_statistics.assert_called_once()
