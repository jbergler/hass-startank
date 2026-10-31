"""STAR-Tank sensor entities.

All values are derived from the latest decoded BLE advertisement held by
`StarTankCoordinator`. Nothing polls — entities update when the next advert
arrives (~every 60 s).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    UnitOfElectricPotential,
    UnitOfLength,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_DEAD_ZONE_CM,
    CONF_FULL_OFFSET_CM,
    CONF_TANK_HEIGHT_CM,
    DEFAULT_DEAD_ZONE_CM,
    DEFAULT_FULL_OFFSET_CM,
    DEFAULT_TANK_HEIGHT_CM,
    DOMAIN,
)
from .coordinator import StarTankCoordinator
from .entity import StarTankEntity
from .parser import StarTankReading


@dataclass(frozen=True, kw_only=True)
class StarTankSensorDescription(SensorEntityDescription):
    """Describe a STAR-Tank sensor and how to pull its value."""

    value: Callable[[StarTankReading], float | int | None]


_READING_SENSORS: tuple[StarTankSensorDescription, ...] = (
    StarTankSensorDescription(
        key="distance",
        translation_key="distance",
        device_class=SensorDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.CENTIMETERS,
        state_class=SensorStateClass.MEASUREMENT,
        value=lambda r: r.distance_cm,
    ),
    StarTankSensorDescription(
        key="temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value=lambda r: r.temperature_c,
    ),
    StarTankSensorDescription(
        key="battery_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        value=lambda r: round(r.battery_voltage, 2),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add STAR-Tank sensors for one config entry."""
    coordinator: StarTankCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = [
        StarTankSensor(coordinator, entry, desc) for desc in _READING_SENSORS
    ]
    entities.append(StarTankLevelSensor(coordinator, entry))
    entities.append(StarTankLevelPercentSensor(coordinator, entry))
    entities.append(StarTankRssiSensor(coordinator, entry))
    async_add_entities(entities)


class StarTankSensor(StarTankEntity, SensorEntity):
    """A direct passthrough of one decoded reading field."""

    entity_description: StarTankSensorDescription  # ty: ignore[invalid-mutable-override] - HA class attr

    def __init__(
        self,
        coordinator: StarTankCoordinator,
        entry: ConfigEntry,
        description: StarTankSensorDescription,
    ) -> None:
        super().__init__(coordinator, entry, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> float | int | None:  # ty: ignore[invalid-property-type-override] - HA attr
        reading = self.coordinator.data
        if reading is None:
            return None
        return self.entity_description.value(reading)


class _TankGeometryMixin:
    """Shared tank-height arithmetic for level/percent sensors."""

    def __init__(self, entry: ConfigEntry) -> None:
        options = entry.options
        self._tank_height = float(
            options.get(CONF_TANK_HEIGHT_CM, DEFAULT_TANK_HEIGHT_CM)
        )
        self._dead_zone = float(options.get(CONF_DEAD_ZONE_CM, DEFAULT_DEAD_ZONE_CM))
        self._full_offset = float(
            options.get(CONF_FULL_OFFSET_CM, DEFAULT_FULL_OFFSET_CM)
        )

    def _level_cm(self, reading: StarTankReading) -> float | None:
        distance = reading.distance_cm
        # Clamp readings in the dead zone to "full"; the sensor can't resolve
        # anything closer than ~3 cm.
        distance = max(distance, self._dead_zone)
        level = self._tank_height - (distance - self._full_offset)
        return max(0.0, min(self._tank_height, level))


class StarTankLevelSensor(_TankGeometryMixin, StarTankEntity, SensorEntity):
    """Liquid level, derived from distance and configured tank height."""

    _attr_translation_key = "level"
    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_native_unit_of_measurement = UnitOfLength.CENTIMETERS
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: StarTankCoordinator, entry: ConfigEntry) -> None:
        _TankGeometryMixin.__init__(self, entry)
        StarTankEntity.__init__(self, coordinator, entry, "level")

    @property
    def native_value(self) -> float | None:  # ty: ignore[invalid-property-type-override] - HA attr
        reading = self.coordinator.data
        if reading is None:
            return None
        level = self._level_cm(reading)
        return None if level is None else round(level, 1)


class StarTankLevelPercentSensor(_TankGeometryMixin, StarTankEntity, SensorEntity):
    """Liquid level expressed as 0..100 % of the configured tank height."""

    _attr_translation_key = "level_percent"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: StarTankCoordinator, entry: ConfigEntry) -> None:
        _TankGeometryMixin.__init__(self, entry)
        StarTankEntity.__init__(self, coordinator, entry, "level_percent")

    @property
    def native_value(self) -> int | None:  # ty: ignore[invalid-property-type-override] - HA attr
        reading = self.coordinator.data
        if reading is None or self._tank_height <= 0:
            return None
        level = self._level_cm(reading)
        if level is None:
            return None
        return round(level / self._tank_height * 100)


class StarTankRssiSensor(StarTankEntity, SensorEntity):
    """Last-seen advertisement RSSI."""

    _attr_translation_key = "rssi"
    _attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH
    _attr_native_unit_of_measurement = SIGNAL_STRENGTH_DECIBELS_MILLIWATT
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator: StarTankCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "rssi")

    @property
    def native_value(self) -> int | None:  # ty: ignore[invalid-property-type-override] - HA attr
        return self.coordinator.rssi
