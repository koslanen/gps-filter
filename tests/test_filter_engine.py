from datetime import UTC, datetime, timedelta

from custom_components.gps_filter.filter_engine import GPSFilterEngine
from custom_components.gps_filter.models import GPSPoint


def test_first_point():
    engine = GPSFilterEngine()

    point = GPSPoint(
        latitude=60,
        longitude=25,
        accuracy=5,
        timestamp=datetime.now(tz=UTC),
    )

    result = engine.process(point)

    assert result.accepted
    assert result.reason == "first_point"
    assert result.point is point
    assert result.distance_m is None
    assert result.calculated_speed_kmh is None
    assert result.reported_speed_kmh is None


def test_bad_accuracy():
    engine = GPSFilterEngine()

    point = GPSPoint(
        latitude=60,
        longitude=25,
        accuracy=100,
        timestamp=datetime.now(tz=UTC),
    )

    result = engine.process(point)

    assert not result.accepted
    assert result.reason == "accuracy"
    assert result.point is None
    assert result.distance_m is None
    assert result.calculated_speed_kmh is None
    assert result.reported_speed_kmh is None


def test_impossible_jump():
    engine = GPSFilterEngine()

    now = datetime.now(tz=UTC)

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
    assert result.reason == "speed"


def test_duplicate_point_is_rejected():
    engine = GPSFilterEngine()

    first_point = GPSPoint(
        latitude=60,
        longitude=25,
        accuracy=5,
        timestamp=datetime.now(tz=UTC),
    )
    second_point = GPSPoint(
        latitude=60,
        longitude=25,
        accuracy=5,
        timestamp=datetime.now(tz=UTC) + timedelta(seconds=1),
    )

    engine.process(first_point)
    result = engine.process(second_point)

    assert not result.accepted
    assert result.reason == "duplicate"
    assert result.point is None


def test_calculated_speed_and_reported_speed_are_added_to_result():
    engine = GPSFilterEngine()

    first_point = GPSPoint(
        latitude=60.0,
        longitude=25.0,
        accuracy=5,
        timestamp=datetime(2024, 1, 1, tzinfo=UTC),
    )
    second_point = GPSPoint(
        latitude=60.0005,
        longitude=25.0,
        accuracy=5,
        speed=5.0,
        timestamp=datetime(2024, 1, 1, 0, 0, 1, tzinfo=UTC),
    )

    engine.process(first_point)
    result = engine.process(second_point)

    assert result.accepted
    assert result.reason == "accepted"
    assert result.distance_m is not None
    assert result.calculated_speed_kmh is not None
    assert result.reported_speed_kmh == 18.0
    assert result.calculated_speed_kmh > 0


def test_engine_stats_track_decisions():
    engine = GPSFilterEngine(max_speed=50.0, max_accuracy=30.0)

    accepted_point = GPSPoint(
        latitude=60.0,
        longitude=25.0,
        accuracy=5,
        timestamp=datetime(2024, 1, 1, tzinfo=UTC),
    )
    duplicate_point = GPSPoint(
        latitude=60.0,
        longitude=25.0,
        accuracy=5,
        timestamp=datetime(2024, 1, 1, 0, 0, 1, tzinfo=UTC),
    )
    accuracy_point = GPSPoint(
        latitude=61.0,
        longitude=25.0,
        accuracy=100,
        timestamp=datetime(2024, 1, 1, 0, 0, 2, tzinfo=UTC),
    )
    speed_point = GPSPoint(
        latitude=62.0,
        longitude=25.0,
        accuracy=5,
        speed=20.0,
        timestamp=datetime(2024, 1, 1, 0, 0, 3, tzinfo=UTC),
    )

    engine.process(accepted_point)
    engine.process(duplicate_point)
    engine.process(accuracy_point)
    engine.process(speed_point)

    assert engine.stats.accepted == 1
    assert engine.stats.duplicate == 1
    assert engine.stats.accuracy_rejections == 1
    assert engine.stats.speed_rejections == 1
