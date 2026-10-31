"""Constants for the Safiery STAR-Tank integration."""

from __future__ import annotations

DOMAIN = "startank"

# Safiery uses 'GN Hearing' company id (0x0067) for its STAR-Tank adverts.
MANUFACTURER_ID = 0x0067

CONF_TANK_HEIGHT_CM = "tank_height_cm"
CONF_DEAD_ZONE_CM = "dead_zone_cm"
CONF_FULL_OFFSET_CM = "full_offset_cm"

DEFAULT_TANK_HEIGHT_CM = 100.0
# Sensor spec: 3 cm dead zone directly under the puck.
DEFAULT_DEAD_ZONE_CM = 3.0
# Extra distance between sensor face and the "100% full" liquid mark.
DEFAULT_FULL_OFFSET_CM = 0.0
