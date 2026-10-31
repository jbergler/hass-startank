"""Passive BLE listener for one STAR-Tank device.

HA's `bluetooth` component already runs a shared scanner; we register a
callback that fires on every advert that matches our address and manufacturer
id. There is no polling, no connect — advertising-only.
"""

from __future__ import annotations

from collections.abc import Callable
import logging

from homeassistant.components import bluetooth
from homeassistant.components.bluetooth import (
    BluetoothChange,
    BluetoothScanningMode,
    BluetoothServiceInfoBleak,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import MANUFACTURER_ID
from .parser import StarTankReading, decode, nic_matches_address

_LOGGER = logging.getLogger(__name__)


class StarTankCoordinator(DataUpdateCoordinator[StarTankReading | None]):
    """Hold the most recent reading for one STAR-Tank address."""

    def __init__(self, hass: HomeAssistant, address: str) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"startank {address}",
            update_interval=None,  # fully push-driven
        )
        self.address = address.upper()
        self._rssi: int | None = None
        self._unregister: Callable[[], None] | None = None

    @property
    def rssi(self) -> int | None:
        return self._rssi

    async def async_start(self) -> None:
        """Subscribe to matching BLE advertisements."""
        self._unregister = bluetooth.async_register_callback(
            self.hass,
            self._handle_bluetooth_event,
            {
                "address": self.address,
                "manufacturer_id": MANUFACTURER_ID,
                "connectable": False,
            },
            BluetoothScanningMode.PASSIVE,
        )

    async def async_stop(self) -> None:
        """Unsubscribe."""
        if self._unregister is not None:
            self._unregister()
            self._unregister = None

    @callback
    def _handle_bluetooth_event(
        self,
        service_info: BluetoothServiceInfoBleak,
        change: BluetoothChange,
    ) -> None:
        """Decode one incoming advertisement and push it to entities."""
        data = service_info.manufacturer_data.get(MANUFACTURER_ID)
        if not data:
            return
        reading = decode(data)
        if reading is None:
            return
        if not nic_matches_address(reading, service_info.address):
            _LOGGER.debug(
                "Ignoring advert from %s: NIC %s does not match address",
                service_info.address,
                reading.nic_last3,
            )
            return
        self._rssi = service_info.rssi
        self.async_set_updated_data(reading)
