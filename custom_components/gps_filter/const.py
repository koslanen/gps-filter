"""Constants for GPS Filter."""

from typing import Final

DOMAIN: Final = "gps_filter"

CONF_SOURCE: Final = "source"
CONF_MAX_SPEED: Final = "max_speed"
CONF_MAX_ACCURACY: Final = "max_accuracy"

DEFAULT_MAX_SPEED: Final = 220.0
DEFAULT_MAX_ACCURACY: Final = 30.0

PLATFORMS: Final = ["device_tracker", "sensor"]
