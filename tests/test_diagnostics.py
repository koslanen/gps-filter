import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import homeassistant.helpers.frame as frame
import pytest

from custom_components.gps_filter.const import VERSION
from custom_components.gps_filter.coordinator import GPSFilterCoordinator
from custom_components.gps_filter.diagnostics import (
    async_get_config_entry_diagnostics,
)
from custom_components.gps_filter.models import (
    CoordinatorData,
    EngineStats,
    FilterResult,
    GPSPoint,
)


@pytest.fixture(autouse=True)
def _disable_frame_reporting(monkeypatch):
    monkeypatch.setattr(frame, "report_usage", lambda *args, **kwargs: None)


class DummyEntry:
    def __init__(self, options=None) -> None:
        self.entry_id = "entry-1"
        self.data = {
            "source": "device_tracker.test",
            "max_speed": 220.0,
            "max_accuracy": 30.0,
            "max_speed_difference_kmh": 40.0,
        }
        self.options = options or {}


def test_diagnostics_report_contains_expected_fields():
    coordinator = GPSFilterCoordinator(hass=Mock(), entry=DummyEntry())
    coordinator.data = CoordinatorData(
        last_received_point=GPSPoint(
            latitude=60.0,
            longitude=25.0,
            accuracy=5.0,
            timestamp=datetime(2024, 1, 1, tzinfo=UTC),
        ),
        last_accepted_point=GPSPoint(
            latitude=60.0,
            longitude=25.0,
            accuracy=5.0,
            timestamp=datetime(2024, 1, 1, tzinfo=UTC),
        ),
        last_result=FilterResult(
            accepted=True,
            reason="accepted",
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
    coordinator.summary_stats.total_received_count = 10
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

    hass = SimpleNamespace(data={"gps_filter": {"entry-1": coordinator}})
    entry = DummyEntry()

    result = asyncio.run(async_get_config_entry_diagnostics(hass, entry))

    assert result["version"] == "0.0.1"
    assert result["configuration"]["source"] == "<redacted>"
    assert result["effective_filter_config"] == {
        "max_speed": 220.0,
        "max_accuracy": 30.0,
        "max_speed_difference_kmh": 40.0,
        "startup_max_accuracy": 10.0,
        "gap_accepted_seconds": 120.0,
    }
    assert result["accepted_count"] == 2
    assert result["duplicate_count"] == 1
    assert result["accuracy_rejections"] == 3
    assert result["startup_accuracy_rejections"] == 6
    assert result["speed_rejections"] == 4
    assert result["speed_consistency_rejections"] == 5
    assert result["gap_accepted_count"] == 6
    assert result["summary"] == {
        "total_received_count": 10,
        "total_rejected_count": 19,
        "accepted_count": 2,
        "duplicate_count": 1,
        "accuracy_rejections": 3,
        "startup_accuracy_rejections": 6,
        "speed_rejections": 4,
        "speed_consistency_rejections": 5,
        "gap_accepted_count": 6,
        "acceptance_rate_percent": 20.0,
        "max_distance_m": 88.0,
        "max_calculated_speed_kmh": 40.0,
        "max_reported_speed_kmh": 36.0,
        "max_accuracy_m": 25.0,
        "max_rejected_distance_m": 100.0,
        "max_rejected_calculated_speed_kmh": 300.0,
        "max_rejected_reported_speed_kmh": 97.2,
        "max_rejected_accuracy_m": 98.0,
        "max_gap_distance_m": 200.0,
        "max_gap_seconds_since_last_accepted": 130.5,
    }
    assert result["last_received_point"]["latitude"] == 60.0
    assert result["last_accepted_point"]["latitude"] == 60.0
    assert result["last_filter_result"]["reason"] == "accepted"
    assert result["last_filter_result"]["seconds_since_last_accepted"] == 5.0
    assert result["filter_timeline"] == []


def test_diagnostics_report_uses_effective_options():
    coordinator = GPSFilterCoordinator(
        hass=Mock(),
        entry=DummyEntry(
            options={
                "max_speed": 120.0,
                "max_accuracy": 15.0,
                "max_speed_difference_kmh": 30.0,
            }
        ),
    )

    hass = SimpleNamespace(data={"gps_filter": {"entry-1": coordinator}})
    entry = DummyEntry(
        options={
            "max_speed": 120.0,
            "max_accuracy": 15.0,
            "max_speed_difference_kmh": 30.0,
        }
    )

    result = asyncio.run(async_get_config_entry_diagnostics(hass, entry))

    assert result["effective_filter_config"] == {
        "max_speed": 120.0,
        "max_accuracy": 15.0,
        "max_speed_difference_kmh": 30.0,
        "startup_max_accuracy": 10.0,
        "gap_accepted_seconds": 120.0,
    }


def test_diagnostics_report_contains_filter_timeline():
    coordinator = GPSFilterCoordinator(hass=Mock(), entry=DummyEntry())
    first_state = SimpleNamespace(
        attributes={
            "latitude": 60.0,
            "longitude": 25.0,
            "gps_accuracy": 5.0,
            "speed": 0.0,
        },
        last_updated=datetime(2024, 1, 1, tzinfo=UTC),
    )
    second_state = SimpleNamespace(
        attributes={
            "latitude": 60.0,
            "longitude": 25.0,
            "gps_accuracy": 5.0,
            "speed": 0.0,
        },
        last_updated=datetime(2024, 1, 1, 0, 0, 1, tzinfo=UTC),
    )
    coordinator._state_changed(SimpleNamespace(data={"new_state": first_state}))
    coordinator._state_changed(SimpleNamespace(data={"new_state": second_state}))

    hass = SimpleNamespace(data={"gps_filter": {"entry-1": coordinator}})
    entry = DummyEntry()

    result = asyncio.run(async_get_config_entry_diagnostics(hass, entry))

    assert result["filter_timeline"] == [
        {
            "timestamp": "2024-01-01T00:00:00+00:00",
            "accepted": True,
            "reason": "first_point",
            "latitude": 60.0,
            "longitude": 25.0,
            "accuracy": 5.0,
            "distance_m": None,
            "calculated_speed_kmh": None,
            "reported_speed_kmh": None,
            "seconds_since_last_accepted": None,
        },
        {
            "timestamp": "2024-01-01T00:00:01+00:00",
            "accepted": False,
            "reason": "duplicate",
            "latitude": 60.0,
            "longitude": 25.0,
            "accuracy": 5.0,
            "distance_m": 0.0,
            "calculated_speed_kmh": 0.0,
            "reported_speed_kmh": 0.0,
            "seconds_since_last_accepted": 1.0,
        },
    ]
    assert result["summary"]["total_received_count"] == 2
    assert result["summary"]["total_rejected_count"] == 1
    assert result["summary"]["accepted_count"] == 1
    assert result["summary"]["duplicate_count"] == 1
    assert result["summary"]["speed_consistency_rejections"] == 0
    assert result["summary"]["startup_accuracy_rejections"] == 0
    assert result["summary"]["gap_accepted_count"] == 0
    assert result["summary"]["acceptance_rate_percent"] == 50.0
    assert result["summary"]["max_accuracy_m"] == 5.0
    assert result["summary"]["max_rejected_accuracy_m"] == 5.0
    assert result["summary"]["max_gap_distance_m"] == 0.0
    assert result["summary"]["max_gap_seconds_since_last_accepted"] == 0.0


def test_manifest_version_matches_const_version():
    manifest_path = (
        Path(__file__).resolve().parents[1]
        / "custom_components"
        / "gps_filter"
        / "manifest.json"
    )

    assert json.loads(manifest_path.read_text(encoding="utf-8"))["version"] == VERSION
