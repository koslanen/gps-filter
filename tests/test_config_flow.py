import asyncio

import pytest
import voluptuous as vol

from custom_components.gps_filter.config_flow import (
    GPSFilterConfigFlow,
    GPSFilterOptionsFlow,
    _get_options_schema,
    _get_user_data_schema,
)
from custom_components.gps_filter.const import (
    CONF_MAX_ACCURACY,
    CONF_MAX_SPEED,
    CONF_SOURCE,
    DOMAIN,
)


class DummyEntry:
    def __init__(self, options=None) -> None:
        self.data = {
            CONF_SOURCE: "device_tracker.test",
            CONF_MAX_SPEED: 220.0,
            CONF_MAX_ACCURACY: 30.0,
        }
        self.options = options or {}


def test_config_schema_rejects_zero_or_negative_thresholds():
    schema = _get_user_data_schema()

    with pytest.raises(vol.Invalid):
        schema(
            {
                CONF_SOURCE: "device_tracker.test",
                CONF_MAX_SPEED: 0,
                CONF_MAX_ACCURACY: 30,
            }
        )

    with pytest.raises(vol.Invalid):
        schema(
            {
                CONF_SOURCE: "device_tracker.test",
                CONF_MAX_SPEED: 220,
                CONF_MAX_ACCURACY: -1,
            }
        )


def test_config_schema_accepts_positive_thresholds():
    schema = _get_user_data_schema()

    result = schema(
        {
            CONF_SOURCE: "device_tracker.test",
            CONF_MAX_SPEED: "120.5",
            CONF_MAX_ACCURACY: "15",
        }
    )

    assert result[CONF_MAX_SPEED] == 120.5
    assert result[CONF_MAX_ACCURACY] == 15.0


def test_options_schema_uses_existing_options_as_defaults():
    schema = _get_options_schema(
        {
            CONF_MAX_SPEED: 100.0,
            CONF_MAX_ACCURACY: 10.0,
        }
    )

    max_speed_marker = next(
        marker
        for marker in schema.schema
        if marker.schema == CONF_MAX_SPEED
    )
    max_accuracy_marker = next(
        marker
        for marker in schema.schema
        if marker.schema == CONF_MAX_ACCURACY
    )

    assert max_speed_marker.default() == 100.0
    assert max_accuracy_marker.default() == 10.0


def test_options_schema_rejects_zero_or_negative_thresholds():
    schema = _get_options_schema(
        {
            CONF_MAX_SPEED: 100.0,
            CONF_MAX_ACCURACY: 10.0,
        }
    )

    with pytest.raises(vol.Invalid):
        schema(
            {
                CONF_MAX_SPEED: 100.0,
                CONF_MAX_ACCURACY: 0,
            }
        )

    with pytest.raises(vol.Invalid):
        schema(
            {
                CONF_MAX_SPEED: -1,
                CONF_MAX_ACCURACY: 10.0,
            }
        )


def test_config_flow_creates_options_flow():
    flow = GPSFilterConfigFlow.async_get_options_flow(DummyEntry())

    assert isinstance(flow, GPSFilterOptionsFlow)


def test_options_flow_saves_positive_thresholds():
    flow = GPSFilterOptionsFlow(DummyEntry())
    flow.flow_id = "test-flow"
    flow.handler = DOMAIN
    flow.context = {}

    result = asyncio.run(
        flow.async_step_init(
            {
                CONF_MAX_SPEED: 130.0,
                CONF_MAX_ACCURACY: 12.0,
            }
        )
    )

    assert result["type"] == "create_entry"
    assert result["data"] == {
        CONF_MAX_SPEED: 130.0,
        CONF_MAX_ACCURACY: 12.0,
    }


def test_options_flow_form_uses_data_fallbacks():
    flow = GPSFilterOptionsFlow(DummyEntry())
    flow.flow_id = "test-flow"
    flow.handler = DOMAIN
    flow.context = {}

    result = asyncio.run(flow.async_step_init())

    assert result["type"] == "form"
    assert result["step_id"] == "init"
