"""Constants for GPS Filter."""

from typing import Final

DOMAIN: Final = "gps_filter"
VERSION: Final = "0.0.1"

CONF_SOURCE: Final = "source"
CONF_MAX_SPEED: Final = "max_speed"
CONF_MAX_ACCURACY: Final = "max_accuracy"
CONF_MAX_SPEED_DIFFERENCE: Final = "max_speed_difference_kmh"

DEFAULT_MAX_SPEED: Final = 220.0
DEFAULT_MAX_ACCURACY: Final = 30.0
DEFAULT_MAX_SPEED_DIFFERENCE: Final = 40.0

PLATFORMS: Final = ["button", "device_tracker", "sensor"]
