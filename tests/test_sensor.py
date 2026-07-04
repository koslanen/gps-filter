from unittest.mock import Mock

import homeassistant.helpers.frame as frame
import pytest

from custom_components.gps_filter.coordinator import GPSFilterCoordinator
from custom_components.gps_filter.models import (
    CoordinatorData,
    EngineStats,
    FilterResult,
)
from custom_components.gps_filter.sensor import (
    GPSFilterAcceptedCountSensor,
    GPSFilterAccuracyRejectionsSensor,
    GPSFilterCalculatedSpeedSensor,
    GPSFilterDistanceSensor,
    GPSFilterDuplicateCountSensor,
    GPSFilterLastAccuracySensor,
    GPSFilterLastReasonSensor,
    GPSFilterReportedSpeedSensor,
    GPSFilterSpeedRejectionsSensor,
    GPSFilterStatusSensor,
)


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


def test_sensor_entities_expose_coordinator_state():
    coordinator = GPSFilterCoordinator(hass=Mock(), entry=DummyEntry())
    coordinator.data = CoordinatorData(
        last_received_point=Mock(accuracy=5.0),
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

    status_sensor = GPSFilterStatusSensor(coordinator)
    calculated_speed_sensor = GPSFilterCalculatedSpeedSensor(coordinator)
    reported_speed_sensor = GPSFilterReportedSpeedSensor(coordinator)
    distance_sensor = GPSFilterDistanceSensor(coordinator)
    accepted_count_sensor = GPSFilterAcceptedCountSensor(coordinator)
    duplicate_count_sensor = GPSFilterDuplicateCountSensor(coordinator)
    accuracy_rejections_sensor = GPSFilterAccuracyRejectionsSensor(coordinator)
    speed_rejections_sensor = GPSFilterSpeedRejectionsSensor(coordinator)
    last_reason_sensor = GPSFilterLastReasonSensor(coordinator)
    last_accuracy_sensor = GPSFilterLastAccuracySensor(coordinator)

    assert status_sensor.native_value == "accepted"
    assert calculated_speed_sensor.native_value == 12.5
    assert reported_speed_sensor.native_value == 10.0
    assert distance_sensor.native_value == 42.0
    assert accepted_count_sensor.native_value == 2
    assert duplicate_count_sensor.native_value == 1
    assert accuracy_rejections_sensor.native_value == 3
    assert speed_rejections_sensor.native_value == 4
    assert last_reason_sensor.native_value == "accepted"
    assert last_accuracy_sensor.native_value == 5.0


def test_sensor_entities_default_to_valid_dashboard_states():
    coordinator = GPSFilterCoordinator(hass=Mock(), entry=DummyEntry())
    coordinator.data = CoordinatorData(engine_stats=EngineStats())

    status_sensor = GPSFilterStatusSensor(coordinator)
    calculated_speed_sensor = GPSFilterCalculatedSpeedSensor(coordinator)
    reported_speed_sensor = GPSFilterReportedSpeedSensor(coordinator)
    distance_sensor = GPSFilterDistanceSensor(coordinator)
    accepted_count_sensor = GPSFilterAcceptedCountSensor(coordinator)
    duplicate_count_sensor = GPSFilterDuplicateCountSensor(coordinator)
    accuracy_rejections_sensor = GPSFilterAccuracyRejectionsSensor(coordinator)
    speed_rejections_sensor = GPSFilterSpeedRejectionsSensor(coordinator)
    last_reason_sensor = GPSFilterLastReasonSensor(coordinator)
    last_accuracy_sensor = GPSFilterLastAccuracySensor(coordinator)

    assert status_sensor.native_value == "unknown"
    assert calculated_speed_sensor.native_value == 0.0
    assert reported_speed_sensor.native_value == 0.0
    assert distance_sensor.native_value == 0.0
    assert accepted_count_sensor.native_value == 0
    assert duplicate_count_sensor.native_value == 0
    assert accuracy_rejections_sensor.native_value == 0
    assert speed_rejections_sensor.native_value == 0
    assert last_reason_sensor.native_value == "unknown"
    assert last_accuracy_sensor.native_value == 0.0
