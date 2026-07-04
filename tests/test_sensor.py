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
    "sensor.gps_filter_distance",
    "sensor.gps_filter_calculated_speed",
    "sensor.gps_filter_reported_speed",
    "sensor.gps_filter_last_reason",
    "sensor.gps_filter_last_accuracy",
    "sensor.gps_filter_last_received_timestamp",
    "sensor.gps_filter_last_accepted_timestamp",
    "sensor.gps_filter_accepted_count",
    "sensor.gps_filter_duplicate_count",
    "sensor.gps_filter_accuracy_rejections",
    "sensor.gps_filter_speed_rejections",
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
        ),
        engine_stats=EngineStats(
            accepted=2,
            duplicate=1,
            accuracy_rejections=3,
            speed_rejections=4,
        ),
    )
    coordinator.data.last_received_point.timestamp = datetime(
        2024,
        1,
        1,
        tzinfo=UTC,
    )

    sensors = _make_sensors(coordinator)

    assert sensors["status"].native_value == "accepted"
    assert sensors["distance"].native_value == 42.0
    assert sensors["calculated_speed"].native_value == 12.5
    assert sensors["reported_speed"].native_value == 10.0
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
    assert sensors["accepted_count"].native_value == 2
    assert sensors["duplicate_count"].native_value == 1
    assert sensors["accuracy_rejections"].native_value == 3
    assert sensors["speed_rejections"].native_value == 4


def test_sensor_entities_default_to_valid_dashboard_states():
    coordinator = GPSFilterCoordinator(hass=Mock(), entry=DummyEntry())
    coordinator.data = CoordinatorData(engine_stats=EngineStats())

    sensors = _make_sensors(coordinator)

    assert sensors["status"].native_value == "unknown"
    assert sensors["distance"].native_value == 0.0
    assert sensors["calculated_speed"].native_value == 0.0
    assert sensors["reported_speed"].native_value == 0.0
    assert sensors["last_reason"].native_value == "unknown"
    assert sensors["last_accuracy"].native_value == 0.0
    assert sensors["last_received_timestamp"].native_value is None
    assert sensors["last_accepted_timestamp"].native_value is None
    assert sensors["accepted_count"].native_value == 0
    assert sensors["duplicate_count"].native_value == 0
    assert sensors["accuracy_rejections"].native_value == 0
    assert sensors["speed_rejections"].native_value == 0


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
        "distance": None,
        "calculated_speed": None,
        "reported_speed": None,
        "last_reason": None,
        "last_accuracy": None,
        "last_received_timestamp": None,
        "last_accepted_timestamp": None,
        "accepted_count": SensorStateClass.TOTAL_INCREASING,
        "duplicate_count": SensorStateClass.TOTAL_INCREASING,
        "accuracy_rejections": SensorStateClass.TOTAL_INCREASING,
        "speed_rejections": SensorStateClass.TOTAL_INCREASING,
    }
