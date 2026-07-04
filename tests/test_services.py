from unittest.mock import Mock

import homeassistant.helpers.frame as frame
import pytest

from custom_components.gps_filter import _iter_coordinators
from custom_components.gps_filter.coordinator import GPSFilterCoordinator


class DummyEntry:
    def __init__(self) -> None:
        self.entry_id = "entry-1"
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
