"""GPS filtering engine."""

from __future__ import annotations

from math import asin, cos, radians, sin, sqrt

from .models import FilterResult, GPSPoint

EARTH_RADIUS = 6371000.0


def haversine(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:
    """Return distance in metres."""

    d_lat = radians(lat2 - lat1)
    d_lon = radians(lon2 - lon1)

    lat1 = radians(lat1)
    lat2 = radians(lat2)

    a = sin(d_lat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(d_lon / 2) ** 2

    c = 2 * asin(sqrt(a))

    return EARTH_RADIUS * c


class GPSFilterEngine:
    """Filter GPS updates."""

    def __init__(
        self,
        *,
        max_speed: float = 220.0,
        max_accuracy: float = 30.0,
        max_jump: float = 1000.0,
    ) -> None:

        self._max_speed = max_speed
        self._max_accuracy = max_accuracy
        self._max_jump = max_jump

        self._last_point: GPSPoint | None = None

    def process(
        self,
        point: GPSPoint,
    ) -> FilterResult:
        """Process a point."""

        if point.accuracy > self._max_accuracy:
            return FilterResult(
                accepted=False,
                reason="accuracy",
                point=None,
            )

        if self._last_point is None:
            self._last_point = point

            return FilterResult(
                accepted=True,
                reason=None,
                point=point,
            )

        distance = haversine(
            self._last_point.latitude,
            self._last_point.longitude,
            point.latitude,
            point.longitude,
        )

        seconds = (point.timestamp - self._last_point.timestamp).total_seconds()

        if seconds <= 0:
            seconds = 1

        speed = distance / seconds * 3.6

        if distance > self._max_jump:
            return FilterResult(
                accepted=False,
                reason="jump",
                point=None,
                calculated_speed=speed,
                jump_distance=distance,
            )

        if speed > self._max_speed:
            return FilterResult(
                accepted=False,
                reason="speed",
                point=None,
                calculated_speed=speed,
                jump_distance=distance,
            )

        self._last_point = point

        return FilterResult(
            accepted=True,
            reason=None,
            point=point,
            calculated_speed=speed,
            jump_distance=distance,
        )
