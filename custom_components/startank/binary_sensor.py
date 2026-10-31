"""STAR-Tank binary sensor entities (low battery, sync button)."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import StarTankCoordinator
from .entity import StarTankEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add STAR-Tank binary sensors."""
    coordinator: StarTankCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            StarTankLowBattery(coordinator, entry),
            StarTankSyncButton(coordinator, entry),
        ]
    )


class StarTankLowBattery(StarTankEntity, BinarySensorEntity):
    """Battery voltage below ~2.3 V (≈15 % of a CR2477's usable span)."""

    _attr_translation_key = "low_battery"
    _attr_device_class = BinarySensorDeviceClass.BATTERY

    def __init__(self, coordinator: StarTankCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "low_battery")

    @property
    def is_on(self) -> bool | None:  # ty: ignore[invalid-property-type-override] - HA attr
        reading = self.coordinator.data
        return None if reading is None else reading.low_battery


class StarTankSyncButton(StarTankEntity, BinarySensorEntity):
    """Reflects the physical sync button bit from the latest advert."""

    _attr_translation_key = "sync_button"
    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator: StarTankCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "sync_button")

    @property
    def is_on(self) -> bool | None:  # ty: ignore[invalid-property-type-override] - HA attr
        reading = self.coordinator.data
        return None if reading is None else reading.sync_button
