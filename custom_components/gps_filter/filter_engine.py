"""GPS filtering engine."""

from __future__ import annotations

from math import asin, cos, radians, sin, sqrt

from .const import DEFAULT_STARTUP_MAX_ACCURACY, GAP_ACCEPTED_SECONDS
from .models import EngineStats, FilterResult, GPSPoint

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
        max_speed_difference_kmh: float = 40.0,
        startup_max_accuracy: float = DEFAULT_STARTUP_MAX_ACCURACY,
    ) -> None:

        self._max_speed = max_speed
        self._max_accuracy = max_accuracy
        self._max_speed_difference_kmh = max_speed_difference_kmh
        self._startup_max_accuracy = startup_max_accuracy

        self._last_point: GPSPoint | None = None
        self.stats = EngineStats()

    def process(
        self,
        point: GPSPoint,
    ) -> FilterResult:
        """Process a point."""

        if point.accuracy > self._max_accuracy:
            self.stats.accuracy_rejections += 1
            return FilterResult(
                accepted=False,
                reason="accuracy",
                point=None,
            )

        if self._last_point is None:
            if point.accuracy > self._startup_max_accuracy:
                self.stats.startup_accuracy_rejections += 1
                return FilterResult(
                    accepted=False,
                    reason="startup_accuracy",
                    point=None,
                )

            self._last_point = point
            self.stats.accepted += 1

            return FilterResult(
                accepted=True,
                reason="first_point",
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

        calculated_speed_kmh = distance / seconds * 3.6
        reported_speed_kmh = point.speed * 3.6 if point.speed is not None else None

        if (
            point.latitude == self._last_point.latitude
            and point.longitude == self._last_point.longitude
        ):
            self.stats.duplicate += 1
            return FilterResult(
                accepted=False,
                reason="duplicate",
                point=None,
                distance_m=0.0,
                calculated_speed_kmh=0.0,
                reported_speed_kmh=reported_speed_kmh,
                seconds_since_last_accepted=seconds,
            )

        if calculated_speed_kmh > self._max_speed:
            self.stats.speed_rejections += 1
            return FilterResult(
                accepted=False,
                reason="speed",
                point=None,
                distance_m=distance,
                calculated_speed_kmh=calculated_speed_kmh,
                reported_speed_kmh=reported_speed_kmh,
                seconds_since_last_accepted=seconds,
            )

        if (
            reported_speed_kmh is not None
            and abs(calculated_speed_kmh - reported_speed_kmh)
            > self._max_speed_difference_kmh
        ):
            self.stats.speed_consistency_rejections += 1
            return FilterResult(
                accepted=False,
                reason="speed_consistency",
                point=None,
                distance_m=distance,
                calculated_speed_kmh=calculated_speed_kmh,
                reported_speed_kmh=reported_speed_kmh,
                seconds_since_last_accepted=seconds,
            )

        self._last_point = point
        self.stats.accepted += 1
        reason = "accepted"
        if seconds > GAP_ACCEPTED_SECONDS:
            self.stats.gap_accepted += 1
            reason = "gap_accepted"

        return FilterResult(
            accepted=True,
            reason=reason,
            point=point,
            distance_m=distance,
            calculated_speed_kmh=calculated_speed_kmh,
            reported_speed_kmh=reported_speed_kmh,
            seconds_since_last_accepted=seconds,
        )
