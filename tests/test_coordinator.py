from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import Mock

import homeassistant.helpers.frame as frame
import pytest

from custom_components.gps_filter.coordinator import GPSFilterCoordinator
from custom_components.gps_filter.device_tracker import FilteredTracker


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
    assert coordinator.data.engine_stats.accepted == 1
    assert coordinator.data.engine_stats.accuracy_rejections == 1


def test_filtered_tracker_exposes_filter_metrics_as_attributes():
    coordinator = GPSFilterCoordinator(hass=Mock(), entry=DummyEntry())
    tracker = FilteredTracker(coordinator)

    coordinator.data.engine_stats.accepted = 2
    coordinator.data.engine_stats.duplicate = 1
    coordinator.data.engine_stats.accuracy_rejections = 3
    coordinator.data.engine_stats.speed_rejections = 4

    coordinator.data.last_result = type(
        "Result",
        (),
        {
            "accepted": True,
            "reason": "accepted",
            "calculated_speed_kmh": 12.5,
            "reported_speed_kmh": 10.0,
            "distance_m": 42.0,
        },
    )()

    attributes = tracker.extra_state_attributes

    assert attributes["accepted_count"] == 2
    assert attributes["duplicate_count"] == 1
    assert attributes["accuracy_rejections"] == 3
    assert attributes["speed_rejections"] == 4
    assert attributes["last_result_reason"] == "accepted"
    assert attributes["last_result_accepted"] is True
    assert attributes["last_distance_m"] == 42.0
    assert attributes["last_calculated_speed_kmh"] == 12.5
    assert attributes["last_reported_speed_kmh"] == 10.0
    assert attributes["last_received_accuracy"] is None
    assert attributes["last_received_timestamp"] is None


def test_coordinator_reset_statistics_and_filter_state():
    coordinator = GPSFilterCoordinator(hass=Mock(), entry=DummyEntry())
    coordinator.data.last_received_point = Mock()
    coordinator.data.last_accepted_point = Mock()
    coordinator.data.last_result = Mock()
    coordinator.data.engine_stats.accepted = 1
    coordinator.data.engine_stats.duplicate = 1
    coordinator.data.engine_stats.accuracy_rejections = 1
    coordinator.data.engine_stats.speed_rejections = 1

    coordinator.reset_statistics()

    assert coordinator.data.engine_stats.accepted == 0
    assert coordinator.data.engine_stats.duplicate == 0
    assert coordinator.data.engine_stats.accuracy_rejections == 0
    assert coordinator.data.engine_stats.speed_rejections == 0

    coordinator.reset_filter()

    assert coordinator.data.last_received_point is None
    assert coordinator.data.last_accepted_point is None
    assert coordinator.data.last_result is None
    assert coordinator.data.engine_stats.accepted == 0
    assert coordinator.data.engine_stats.duplicate == 0
    assert coordinator.data.engine_stats.accuracy_rejections == 0
    assert coordinator.data.engine_stats.speed_rejections == 0
