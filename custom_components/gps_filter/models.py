"""Data models for GPS Filter."""

from __future__ import annotations

from dataclasses import dataclass
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
    reason: str | None
    point: GPSPoint | None
    calculated_speed: float | None = None
    jump_distance: float | None = None


@dataclass(slots=True)
class FilterConfig:
    """Filter configuration."""

    source_entity: str
    max_speed: float
    max_accuracy: float
