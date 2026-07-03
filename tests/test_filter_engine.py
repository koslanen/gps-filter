from datetime import datetime, timedelta

from custom_components.gps_filter.filter_engine import GPSFilterEngine
from custom_components.gps_filter.models import GPSPoint


def test_first_point():
    engine = GPSFilterEngine()

    point = GPSPoint(
        latitude=60,
        longitude=25,
        accuracy=5,
        timestamp=datetime.now(),
    )

    result = engine.process(point)

    assert result.accepted


def test_bad_accuracy():
    engine = GPSFilterEngine()

    point = GPSPoint(
        latitude=60,
        longitude=25,
        accuracy=100,
        timestamp=datetime.now(),
    )

    result = engine.process(point)

    assert not result.accepted
    assert result.reason == "accuracy"


def test_impossible_jump():
    engine = GPSFilterEngine()

    now = datetime.now()

    engine.process(
        GPSPoint(
            60,
            25,
            5,
            now,
        )
    )

    result = engine.process(
        GPSPoint(
            61,
            26,
            5,
            now + timedelta(seconds=5),
        )
    )

    assert not result.accepted