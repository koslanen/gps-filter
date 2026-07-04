"""Data models for GPS Filter."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True)
class GPSPoint:
    """A GPS point."""

    latitude: float
    longitude: float
    accuracy: float
    timestamp: datetime
    speed: float | None = None
    course: float | None = None


@dataclass(slots=True)
class FilterResult:
    """Result of processing a GPS point."""

    accepted: bool
    reason: str = ""
    point: GPSPoint | None = None
    distance_m: float | None = None
    calculated_speed_kmh: float | None = None
    reported_speed_kmh: float | None = None


@dataclass(slots=True)
class EngineStats:
    """Statistics for GPS filter decisions."""

    accepted: int = 0
    duplicate: int = 0
    accuracy_rejections: int = 0
    speed_rejections: int = 0


@dataclass(slots=True)
class CoordinatorData:
    """Structured snapshot of coordinator state."""

    last_received_point: GPSPoint | None = None
    last_accepted_point: GPSPoint | None = None
    last_result: FilterResult | None = None
    engine_stats: EngineStats = field(default_factory=EngineStats)


@dataclass(slots=True)
class FilterConfig:
    """Filter configuration."""

    source_entity: str
    max_speed: float
    max_accuracy: float
