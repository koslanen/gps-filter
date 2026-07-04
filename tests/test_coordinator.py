from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import Mock

import homeassistant.helpers.frame as frame
import pytest

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


def test_coordinator_updates_last_received_and_preserves_last_accepted_on_rejection():
    coordinator = GPSFilterCoordinator(hass=Mock(), entry=DummyEntry())

    accepted_state = SimpleNamespace(
        attributes={
            "latitude": 60.0,
            "longitude": 25.0,
            "gps_accuracy": 5.0,
            "speed": 0.0,
        },
        last_updated=datetime(2024, 1, 1, tzinfo=UTC),
    )

    coordinator._state_changed(SimpleNamespace(data={"new_state": accepted_state}))

    assert coordinator.last_received_point is not None
    assert coordinator.last_received_point.latitude == 60.0
    assert coordinator.last_accepted_point is not None
    assert coordinator.last_accepted_point.latitude == 60.0
    assert coordinator.last_result is not None
    assert coordinator.last_result.accepted is True

    rejected_state = SimpleNamespace(
        attributes={
            "latitude": 61.0,
            "longitude": 26.0,
            "gps_accuracy": 100.0,
            "speed": 0.0,
        },
        last_updated=datetime(2024, 1, 1, 0, 0, 1, tzinfo=UTC),
    )

    coordinator._state_changed(SimpleNamespace(data={"new_state": rejected_state}))

    assert coordinator.last_received_point is not None
    assert coordinator.last_received_point.latitude == 61.0
    assert coordinator.last_accepted_point is not None
    assert coordinator.last_accepted_point.latitude == 60.0
    assert coordinator.last_result is not None
    assert coordinator.last_result.accepted is False
    assert coordinator.last_result.reason == "accuracy"
