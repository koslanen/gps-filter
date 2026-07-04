from types import SimpleNamespace
from unittest.mock import Mock

import homeassistant.helpers.frame as frame
import pytest

from custom_components.gps_filter import (
    _async_handle_reset_filter,
    _async_handle_reset_statistics,
    _iter_coordinators,
)
from custom_components.gps_filter.coordinator import GPSFilterCoordinator


class DummyEntry:
    def __init__(self, entry_id="entry-1") -> None:
        self.entry_id = entry_id
        self.data = {
            "source": "device_tracker.test",
            "max_speed": 220.0,
            "max_accuracy": 30.0,
        }


@pytest.fixture(autouse=True)
def _disable_frame_reporting(monkeypatch):
    monkeypatch.setattr(frame, "report_usage", lambda *args, **kwargs: None)


@pytest.fixture
def hass_with_coordinator():
    hass = Mock()
    hass.data = {"gps_filter": {}}
    coordinator = GPSFilterCoordinator(hass=hass, entry=DummyEntry())
    hass.data["gps_filter"][coordinator.entry.entry_id] = coordinator
    return hass, coordinator


def test_iter_coordinators_returns_loaded_coordinators(hass_with_coordinator):
    hass, coordinator = hass_with_coordinator

    assert _iter_coordinators(hass) == [coordinator]


def test_iter_coordinators_can_filter_by_entry_id():
    hass = Mock()
    hass.data = {"gps_filter": {}}
    first = GPSFilterCoordinator(hass=hass, entry=DummyEntry("entry-1"))
    second = GPSFilterCoordinator(hass=hass, entry=DummyEntry("entry-2"))
    hass.data["gps_filter"][first.entry.entry_id] = first
    hass.data["gps_filter"][second.entry.entry_id] = second

    assert _iter_coordinators(hass, "entry-2") == [second]


def test_reset_services_can_target_one_entry():
    hass = Mock()
    hass.data = {"gps_filter": {}}
    first = GPSFilterCoordinator(hass=hass, entry=DummyEntry("entry-1"))
    second = GPSFilterCoordinator(hass=hass, entry=DummyEntry("entry-2"))
    first.reset_statistics = Mock()
    first.reset_filter = Mock()
    second.reset_statistics = Mock()
    second.reset_filter = Mock()
    hass.data["gps_filter"][first.entry.entry_id] = first
    hass.data["gps_filter"][second.entry.entry_id] = second
    call = SimpleNamespace(hass=hass, data={"entry_id": "entry-2"})

    _async_handle_reset_statistics(call)
    _async_handle_reset_filter(call)

    first.reset_statistics.assert_not_called()
    first.reset_filter.assert_not_called()
    second.reset_statistics.assert_called_once()
    second.reset_filter.assert_called_once()
