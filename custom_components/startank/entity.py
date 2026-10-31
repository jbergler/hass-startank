"""Shared base for STAR-Tank entities."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import StarTankCoordinator


class StarTankEntity(CoordinatorEntity[StarTankCoordinator]):
    """Base entity bound to one STAR-Tank advertisement feed."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: StarTankCoordinator,
        entry: ConfigEntry,
        key: str,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = DeviceInfo(
            connections={(CONNECTION_BLUETOOTH, coordinator.address)},
            identifiers={(DOMAIN, coordinator.address)},
            manufacturer="Safiery",
            model="STAR-Tank",
            name=entry.title,
        )

    @property
    def available(self) -> bool:
        """Entity is available once we have at least one advert."""
        return self.coordinator.data is not None
