from datetime import UTC, datetime
from unittest.mock import Mock

import homeassistant.helpers.frame as frame
import pytest
from homeassistant.components.sensor import SensorStateClass

from custom_components.gps_filter.coordinator import GPSFilterCoordinator
from custom_components.gps_filter.models import (
    CoordinatorData,
    EngineStats,
    FilterResult,
    GPSPoint,
)
from custom_components.gps_filter.sensor import SENSOR_DESCRIPTIONS, GPSFilterSensor

EXPECTED_ENTITY_IDS = [
    "sensor.gps_filter_status",
    "sensor.gps_filter_last_reason",
    "sensor.gps_filter_last_accuracy",
    "sensor.gps_filter_last_received_timestamp",
    "sensor.gps_filter_last_accepted_timestamp",
    "sensor.gps_filter_acceptance_rate",
    "sensor.gps_filter_seconds_since_last_accepted",
    "sensor.gps_filter_total_received_count",
    "sensor.gps_filter_total_rejected_count",
]


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


def _make_sensors(coordinator):
    return {
        description.key: GPSFilterSensor(coordinator, description)
        for description in SENSOR_DESCRIPTIONS
    }


def test_sensor_entities_expose_coordinator_state():
    coordinator = GPSFilterCoordinator(hass=Mock(), entry=DummyEntry())
    coordinator.data = CoordinatorData(
        last_received_point=Mock(accuracy=5.0),
        last_accepted_point=GPSPoint(
            latitude=60.0,
            longitude=25.0,
            accuracy=4.0,
            timestamp=datetime(2024, 1, 1, 0, 0, 1, tzinfo=UTC),
        ),
        last_result=FilterResult(
            accepted=True,
            reason="accepted",
            distance_m=42.0,
            calculated_speed_kmh=12.5,
            reported_speed_kmh=10.0,
            seconds_since_last_accepted=5.0,
        ),
        engine_stats=EngineStats(
            accepted=2,
            duplicate=1,
            accuracy_rejections=3,
            startup_accuracy_rejections=6,
            speed_rejections=4,
            speed_consistency_rejections=5,
            gap_accepted=6,
        ),
    )
    coordinator.summary_stats.total_received_count = 4
    coordinator.summary_stats.max_distance_m = 88.0
    coordinator.summary_stats.max_calculated_speed_kmh = 40.0
    coordinator.summary_stats.max_reported_speed_kmh = 36.0
    coordinator.summary_stats.max_accuracy_m = 25.0
    coordinator.summary_stats.max_rejected_distance_m = 100.0
    coordinator.summary_stats.max_rejected_calculated_speed_kmh = 300.0
    coordinator.summary_stats.max_rejected_reported_speed_kmh = 97.2
    coordinator.summary_stats.max_rejected_accuracy_m = 98.0
    coordinator.summary_stats.max_gap_distance_m = 200.0
    coordinator.summary_stats.max_gap_seconds_since_last_accepted = 130.5
    coordinator.data.last_received_point.timestamp = datetime(
        2024,
        1,
        1,
        tzinfo=UTC,
    )

    sensors = _make_sensors(coordinator)

    assert sensors["status"].native_value == "accepted"
    assert sensors["last_reason"].native_value == "accepted"
    assert sensors["last_accuracy"].native_value == 5.0
    assert sensors["last_received_timestamp"].native_value == datetime(
        2024,
        1,
        1,
        tzinfo=UTC,
    )
    assert sensors["last_accepted_timestamp"].native_value == datetime(
        2024,
        1,
        1,
        0,
        0,
        1,
        tzinfo=UTC,
    )
    assert sensors["acceptance_rate"].native_value == 50.0
    assert sensors["seconds_since_last_accepted"].native_value == 5.0
    assert sensors["total_received_count"].native_value == 4
    assert sensors["total_rejected_count"].native_value == 19


def test_sensor_entities_default_to_valid_dashboard_states():
    coordinator = GPSFilterCoordinator(hass=Mock(), entry=DummyEntry())
    coordinator.data = CoordinatorData(engine_stats=EngineStats())

    sensors = _make_sensors(coordinator)

    assert sensors["status"].native_value == "unknown"
    assert sensors["last_reason"].native_value == "unknown"
    assert sensors["last_accuracy"].native_value == 0.0
    assert sensors["last_received_timestamp"].native_value is None
    assert sensors["last_accepted_timestamp"].native_value is None
    assert sensors["acceptance_rate"].native_value == 0.0
    assert sensors["seconds_since_last_accepted"].native_value == 0.0
    assert sensors["total_received_count"].native_value == 0
    assert sensors["total_rejected_count"].native_value == 0


def test_sensor_descriptions_follow_home_assistant_entity_id_conventions():
    coordinator = GPSFilterCoordinator(hass=Mock(), entry=DummyEntry())
    sensors = [
        GPSFilterSensor(coordinator, description)
        for description in SENSOR_DESCRIPTIONS
    ]

    expected_keys = [
        entity_id.removeprefix("sensor.gps_filter_")
        for entity_id in EXPECTED_ENTITY_IDS
    ]

    assert [sensor.entity_description.key for sensor in sensors] == expected_keys
    assert [
        sensor.entity_description.translation_key for sensor in sensors
    ] == expected_keys
    assert [sensor.unique_id for sensor in sensors] == [
        f"entry-1_{key}" for key in expected_keys
    ]
    assert all(sensor.has_entity_name for sensor in sensors)
    assert all("_attr_entity_id" not in sensor.__dict__ for sensor in sensors)


def test_sensor_entities_share_gps_filter_device_info():
    coordinator = GPSFilterCoordinator(hass=Mock(), entry=DummyEntry())
    sensor = GPSFilterSensor(coordinator, SENSOR_DESCRIPTIONS[0])

    assert sensor.device_info == {
        "identifiers": {("gps_filter", "entry-1")},
        "name": "GPS Filter - Test Tracker",
        "manufacturer": "GPS Filter",
        "model": "Filtered Tracker",
    }


def test_only_counter_sensors_compile_long_term_statistics():
    state_classes = {
        description.key: description.state_class
        for description in SENSOR_DESCRIPTIONS
    }

    assert state_classes == {
        "status": None,
        "last_reason": None,
        "last_accuracy": None,
        "last_received_timestamp": None,
        "last_accepted_timestamp": None,
        "acceptance_rate": None,
        "seconds_since_last_accepted": None,
        "total_received_count": SensorStateClass.TOTAL_INCREASING,
        "total_rejected_count": SensorStateClass.TOTAL_INCREASING,
    }
