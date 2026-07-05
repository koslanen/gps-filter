import logging
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import Mock

import homeassistant.helpers.frame as frame
import pytest

from custom_components.gps_filter.coordinator import (
    FILTER_TIMELINE_MAXLEN,
    GPSFilterCoordinator,
)
from custom_components.gps_filter.device_tracker import FilteredTracker


class DummyEntry:
    def __init__(self, options=None) -> None:
        self.entry_id = "entry-1"
        self.title = "GPS Filter - Test Tracker"
        self.data = {
            "source": "device_tracker.test",
            "max_speed": 220.0,
            "max_accuracy": 30.0,
            "max_speed_difference_kmh": 40.0,
        }
        self.options = options or {}


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


def test_coordinator_ignores_invalid_tracker_coordinates():
    coordinator = GPSFilterCoordinator(hass=Mock(), entry=DummyEntry())

    invalid_state = SimpleNamespace(
        attributes={
            "latitude": "unknown",
            "longitude": 25.0,
            "gps_accuracy": "unknown",
            "speed": "unknown",
        },
        last_updated=datetime(2024, 1, 1, tzinfo=UTC),
    )

    coordinator._state_changed(SimpleNamespace(data={"new_state": invalid_state}))

    assert coordinator.last_received_point is None
    assert coordinator.last_accepted_point is None
    assert coordinator.last_result is None


def test_coordinator_preserves_missing_speed_as_unknown():
    coordinator = GPSFilterCoordinator(hass=Mock(), entry=DummyEntry())

    state = SimpleNamespace(
        attributes={
            "latitude": 60.0,
            "longitude": 25.0,
            "gps_accuracy": 5.0,
        },
        last_updated=datetime(2024, 1, 1, tzinfo=UTC),
    )

    coordinator._state_changed(SimpleNamespace(data={"new_state": state}))

    assert coordinator.last_received_point is not None
    assert coordinator.last_received_point.speed is None


def test_coordinator_uses_options_for_thresholds():
    coordinator = GPSFilterCoordinator(
        hass=Mock(),
        entry=DummyEntry(
            options={
                "max_speed": 80.0,
                "max_accuracy": 12.0,
                "max_speed_difference_kmh": 25.0,
            }
        ),
    )

    assert coordinator.engine._max_speed == 80.0
    assert coordinator.engine._max_accuracy == 12.0
    assert coordinator.engine._max_speed_difference_kmh == 25.0


def test_coordinator_logs_point_diagnostics_at_debug(caplog):
    coordinator = GPSFilterCoordinator(hass=Mock(), entry=DummyEntry())
    state = SimpleNamespace(
        attributes={
            "latitude": 60.0,
            "longitude": 25.0,
            "gps_accuracy": 5.0,
            "speed": 0.0,
        },
        last_updated=datetime(2024, 1, 1, tzinfo=UTC),
    )

    caplog.set_level(logging.DEBUG, logger="custom_components.gps_filter.coordinator")

    coordinator._state_changed(SimpleNamespace(data={"new_state": state}))

    debug_messages = [
        record.message for record in caplog.records if record.levelno == logging.DEBUG
    ]
    info_messages = [
        record.message for record in caplog.records if record.levelno == logging.INFO
    ]

    assert any(message.startswith("Received:") for message in debug_messages)
    assert any(message.startswith("Accepted point:") for message in debug_messages)
    assert not any(message.startswith("Received:") for message in info_messages)
    assert not any(message.startswith("Accepted point:") for message in info_messages)


def test_coordinator_keeps_bounded_filter_timeline():
    coordinator = GPSFilterCoordinator(hass=Mock(), entry=DummyEntry())

    for index in range(FILTER_TIMELINE_MAXLEN + 5):
        state = SimpleNamespace(
            attributes={
                "latitude": 60.0,
                "longitude": 25.0,
                "gps_accuracy": 5.0,
                "speed": 0.0,
            },
            last_updated=datetime(2024, 1, 1, 0, 0, index, tzinfo=UTC),
        )

        coordinator._state_changed(SimpleNamespace(data={"new_state": state}))

    assert len(coordinator.filter_timeline) == FILTER_TIMELINE_MAXLEN
    assert coordinator.filter_timeline[0].timestamp == datetime(
        2024,
        1,
        1,
        0,
        0,
        5,
        tzinfo=UTC,
    )
    assert coordinator.filter_timeline[-1].timestamp == datetime(
        2024,
        1,
        1,
        0,
        0,
        FILTER_TIMELINE_MAXLEN + 4,
        tzinfo=UTC,
    )


def test_coordinator_filter_timeline_entry_contains_filter_decision_fields():
    coordinator = GPSFilterCoordinator(hass=Mock(), entry=DummyEntry())
    state = SimpleNamespace(
        attributes={
            "latitude": 60.0,
            "longitude": 25.0,
            "gps_accuracy": 5.0,
            "speed": 3.0,
        },
        last_updated=datetime(2024, 1, 1, tzinfo=UTC),
    )

    coordinator._state_changed(SimpleNamespace(data={"new_state": state}))

    entry = coordinator.filter_timeline[-1]
    assert entry.timestamp == datetime(2024, 1, 1, tzinfo=UTC)
    assert entry.accepted is True
    assert entry.reason == "first_point"
    assert entry.latitude == 60.0
    assert entry.longitude == 25.0
    assert entry.accuracy == 5.0
    assert entry.distance_m is None
    assert entry.calculated_speed_kmh is None
    assert entry.reported_speed_kmh is None


def test_coordinator_tracks_post_drive_summary_statistics():
    coordinator = GPSFilterCoordinator(hass=Mock(), entry=DummyEntry())

    states = [
        SimpleNamespace(
            attributes={
                "latitude": 60.0,
                "longitude": 25.0,
                "gps_accuracy": 5.0,
                "speed": 0.0,
            },
            last_updated=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
        ),
        SimpleNamespace(
            attributes={
                "latitude": 60.0,
                "longitude": 25.01,
                "gps_accuracy": 8.0,
                "speed": 10.0,
            },
            last_updated=datetime(2024, 1, 1, 0, 1, 0, tzinfo=UTC),
        ),
        SimpleNamespace(
            attributes={
                "latitude": 60.0,
                "longitude": 25.01,
                "gps_accuracy": 6.0,
                "speed": 3.0,
            },
            last_updated=datetime(2024, 1, 1, 0, 1, 1, tzinfo=UTC),
        ),
        SimpleNamespace(
            attributes={
                "latitude": 60.0,
                "longitude": 25.02,
                "gps_accuracy": 100.0,
                "speed": 0.0,
            },
            last_updated=datetime(2024, 1, 1, 0, 2, 0, tzinfo=UTC),
        ),
    ]

    for state in states:
        coordinator._state_changed(SimpleNamespace(data={"new_state": state}))

    assert coordinator.summary_stats.total_received_count == 4
    assert coordinator.data.engine_stats.accepted == 2
    assert coordinator.data.engine_stats.duplicate == 1
    assert coordinator.data.engine_stats.accuracy_rejections == 1
    assert coordinator.data.engine_stats.startup_accuracy_rejections == 0
    assert coordinator.data.engine_stats.speed_rejections == 0
    assert coordinator.data.engine_stats.speed_consistency_rejections == 0
    assert coordinator.data.engine_stats.gap_accepted == 0
    assert coordinator.acceptance_rate_percent == 50.0
    assert coordinator.summary_stats.max_distance_m > 0
    assert coordinator.summary_stats.max_calculated_speed_kmh > 0
    assert coordinator.summary_stats.max_reported_speed_kmh == 36.0
    assert coordinator.summary_stats.max_accuracy_m == 8.0


def test_rejected_points_do_not_update_summary_max_values():
    coordinator = GPSFilterCoordinator(
        hass=Mock(),
        entry=DummyEntry(
            options={
                "max_speed": 50.0,
                "max_accuracy": 30.0,
            }
        ),
    )

    states = [
        SimpleNamespace(
            attributes={
                "latitude": 60.0,
                "longitude": 25.0,
                "gps_accuracy": 5.0,
                "speed": 5.0,
            },
            last_updated=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
        ),
        SimpleNamespace(
            attributes={
                "latitude": 60.0,
                "longitude": 25.001,
                "gps_accuracy": 6.0,
                "speed": 8.0,
            },
            last_updated=datetime(2024, 1, 1, 0, 1, 0, tzinfo=UTC),
        ),
        SimpleNamespace(
            attributes={
                "latitude": 61.0,
                "longitude": 26.0,
                "gps_accuracy": 98.0,
                "speed": 27.0,
            },
            last_updated=datetime(2024, 1, 1, 0, 2, 0, tzinfo=UTC),
        ),
        SimpleNamespace(
            attributes={
                "latitude": 61.0,
                "longitude": 26.0,
                "gps_accuracy": 1.0,
                "speed": 40.0,
            },
            last_updated=datetime(2024, 1, 1, 0, 2, 1, tzinfo=UTC),
        ),
    ]

    for state in states:
        coordinator._state_changed(SimpleNamespace(data={"new_state": state}))

    assert coordinator.summary_stats.total_received_count == 4
    assert coordinator.total_rejected_count == 2
    assert coordinator.acceptance_rate_percent == 50.0
    assert coordinator.summary_stats.max_accuracy_m == 6.0
    assert coordinator.summary_stats.max_reported_speed_kmh == 28.8
    assert coordinator.summary_stats.max_calculated_speed_kmh < 10.0
    assert coordinator.summary_stats.max_distance_m < 100.0
    assert coordinator.summary_stats.max_rejected_accuracy_m == 98.0
    assert coordinator.summary_stats.max_rejected_reported_speed_kmh == 144.0
    assert coordinator.summary_stats.max_rejected_calculated_speed_kmh > 50.0
    assert coordinator.summary_stats.max_rejected_distance_m > 100.0


def test_reset_filter_clears_filter_timeline():
    coordinator = GPSFilterCoordinator(hass=Mock(), entry=DummyEntry())
    state = SimpleNamespace(
        attributes={
            "latitude": 60.0,
            "longitude": 25.0,
            "gps_accuracy": 5.0,
            "speed": 0.0,
        },
        last_updated=datetime(2024, 1, 1, tzinfo=UTC),
    )

    coordinator._state_changed(SimpleNamespace(data={"new_state": state}))
    coordinator.reset_filter()

    assert len(coordinator.filter_timeline) == 0


def test_filtered_tracker_exposes_filter_metrics_as_attributes():
    coordinator = GPSFilterCoordinator(hass=Mock(), entry=DummyEntry())
    tracker = FilteredTracker(coordinator)

    coordinator.data.engine_stats.accepted = 2
    coordinator.data.engine_stats.duplicate = 1
    coordinator.data.engine_stats.accuracy_rejections = 3
    coordinator.data.engine_stats.startup_accuracy_rejections = 6
    coordinator.data.engine_stats.speed_rejections = 4
    coordinator.data.engine_stats.speed_consistency_rejections = 5
    coordinator.data.engine_stats.gap_accepted = 6

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
    assert attributes["startup_accuracy_rejections"] == 6
    assert attributes["speed_rejections"] == 4
    assert attributes["speed_consistency_rejections"] == 5
    assert attributes["gap_accepted_count"] == 6
    assert attributes["last_result_reason"] == "accepted"
    assert attributes["last_result_accepted"] is True
    assert attributes["last_distance_m"] == 42.0
    assert attributes["last_calculated_speed_kmh"] == 12.5
    assert attributes["last_reported_speed_kmh"] == 10.0
    assert attributes["last_received_accuracy"] is None
    assert attributes["last_received_timestamp"] is None


def test_filtered_tracker_uses_entry_specific_device_info():
    coordinator = GPSFilterCoordinator(hass=Mock(), entry=DummyEntry())
    tracker = FilteredTracker(coordinator)

    assert tracker.device_info == {
        "identifiers": {("gps_filter", "entry-1")},
        "name": "GPS Filter - Test Tracker",
        "manufacturer": "GPS Filter",
        "model": "Filtered Tracker",
    }


def test_coordinator_reset_statistics_and_filter_state():
    coordinator = GPSFilterCoordinator(hass=Mock(), entry=DummyEntry())
    coordinator.data.last_received_point = Mock()
    coordinator.data.last_accepted_point = Mock()
    coordinator.data.last_result = Mock()
    coordinator.data.engine_stats.accepted = 1
    coordinator.data.engine_stats.duplicate = 1
    coordinator.data.engine_stats.accuracy_rejections = 1
    coordinator.data.engine_stats.startup_accuracy_rejections = 1
    coordinator.data.engine_stats.speed_rejections = 1
    coordinator.data.engine_stats.speed_consistency_rejections = 1
    coordinator.data.engine_stats.gap_accepted = 1
    coordinator.summary_stats.total_received_count = 4
    coordinator.summary_stats.max_distance_m = 42.0
    coordinator.summary_stats.max_calculated_speed_kmh = 12.5
    coordinator.summary_stats.max_reported_speed_kmh = 10.0
    coordinator.summary_stats.max_accuracy_m = 30.0
    coordinator.summary_stats.max_rejected_distance_m = 100.0
    coordinator.summary_stats.max_rejected_calculated_speed_kmh = 300.0
    coordinator.summary_stats.max_rejected_reported_speed_kmh = 97.2
    coordinator.summary_stats.max_rejected_accuracy_m = 98.0

    coordinator.reset_statistics()

    assert coordinator.data.engine_stats.accepted == 0
    assert coordinator.data.engine_stats.duplicate == 0
    assert coordinator.data.engine_stats.accuracy_rejections == 0
    assert coordinator.data.engine_stats.startup_accuracy_rejections == 0
    assert coordinator.data.engine_stats.speed_rejections == 0
    assert coordinator.data.engine_stats.speed_consistency_rejections == 0
    assert coordinator.data.engine_stats.gap_accepted == 0
    assert coordinator.summary_stats.total_received_count == 0
    assert coordinator.acceptance_rate_percent == 0.0
    assert coordinator.total_rejected_count == 0
    assert coordinator.summary_stats.max_distance_m == 0.0
    assert coordinator.summary_stats.max_calculated_speed_kmh == 0.0
    assert coordinator.summary_stats.max_reported_speed_kmh == 0.0
    assert coordinator.summary_stats.max_accuracy_m == 0.0
    assert coordinator.summary_stats.max_rejected_distance_m == 0.0
    assert coordinator.summary_stats.max_rejected_calculated_speed_kmh == 0.0
    assert coordinator.summary_stats.max_rejected_reported_speed_kmh == 0.0
    assert coordinator.summary_stats.max_rejected_accuracy_m == 0.0

    coordinator.summary_stats.total_received_count = 2
    coordinator.summary_stats.max_distance_m = 24.0
    coordinator.summary_stats.max_calculated_speed_kmh = 20.0
    coordinator.summary_stats.max_reported_speed_kmh = 9.0
    coordinator.summary_stats.max_accuracy_m = 15.0
    coordinator.summary_stats.max_rejected_distance_m = 100.0
    coordinator.summary_stats.max_rejected_calculated_speed_kmh = 300.0
    coordinator.summary_stats.max_rejected_reported_speed_kmh = 97.2
    coordinator.summary_stats.max_rejected_accuracy_m = 98.0

    coordinator.reset_filter()

    assert coordinator.data.last_received_point is None
    assert coordinator.data.last_accepted_point is None
    assert coordinator.data.last_result is None
    assert coordinator.data.engine_stats.accepted == 0
    assert coordinator.data.engine_stats.duplicate == 0
    assert coordinator.data.engine_stats.accuracy_rejections == 0
    assert coordinator.data.engine_stats.startup_accuracy_rejections == 0
    assert coordinator.data.engine_stats.speed_rejections == 0
    assert coordinator.data.engine_stats.speed_consistency_rejections == 0
    assert coordinator.data.engine_stats.gap_accepted == 0
    assert coordinator.summary_stats.total_received_count == 0
    assert coordinator.acceptance_rate_percent == 0.0
    assert coordinator.summary_stats.max_distance_m == 0.0
    assert coordinator.summary_stats.max_calculated_speed_kmh == 0.0
    assert coordinator.summary_stats.max_reported_speed_kmh == 0.0
    assert coordinator.summary_stats.max_accuracy_m == 0.0
    assert coordinator.summary_stats.max_rejected_distance_m == 0.0
    assert coordinator.summary_stats.max_rejected_calculated_speed_kmh == 0.0
    assert coordinator.summary_stats.max_rejected_reported_speed_kmh == 0.0
    assert coordinator.summary_stats.max_rejected_accuracy_m == 0.0
