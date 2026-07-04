import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import Mock

import homeassistant.helpers.frame as frame
import pytest

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
    def __init__(self) -> None:
        self.entry_id = "entry-1"
        self.data = {
            "source": "device_tracker.test",
            "max_speed": 220.0,
            "max_accuracy": 30.0,
        }


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
        last_result=FilterResult(accepted=True, reason="accepted"),
        engine_stats=EngineStats(
            accepted=2,
            duplicate=1,
            accuracy_rejections=3,
            speed_rejections=4,
        ),
    )

    hass = SimpleNamespace(data={"gps_filter": {"entry-1": coordinator}})
    entry = DummyEntry()

    result = asyncio.run(async_get_config_entry_diagnostics(hass, entry))

    assert result["version"] == "0.0.1"
    assert result["configuration"]["source"] == "<redacted>"
    assert result["accepted_count"] == 2
    assert result["duplicate_count"] == 1
    assert result["accuracy_rejections"] == 3
    assert result["speed_rejections"] == 4
    assert result["last_received_point"]["latitude"] == 60.0
    assert result["last_accepted_point"]["latitude"] == 60.0
    assert result["last_filter_result"]["reason"] == "accepted"
