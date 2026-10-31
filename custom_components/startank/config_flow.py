"""Config flow for Safiery STAR-Tank.

Two entry points:

- **Bluetooth discovery** — triggered by HA's `bluetooth` component the first
  time a STAR-Tank advertisement is seen. The user confirms + sets tank geometry.
- **User-initiated** — pick from currently-advertising STAR-Tanks.
"""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
)
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import callback

from .const import (
    CONF_DEAD_ZONE_CM,
    CONF_FULL_OFFSET_CM,
    CONF_TANK_HEIGHT_CM,
    DEFAULT_DEAD_ZONE_CM,
    DEFAULT_FULL_OFFSET_CM,
    DEFAULT_TANK_HEIGHT_CM,
    DOMAIN,
    MANUFACTURER_ID,
)
from .parser import PAYLOAD_LEN, decode, nic_matches_address


def _is_startank(service_info: BluetoothServiceInfoBleak) -> bool:
    data = service_info.manufacturer_data.get(MANUFACTURER_ID)
    if not data or len(data) != PAYLOAD_LEN:
        return False
    reading = decode(data)
    return reading is not None and nic_matches_address(reading, service_info.address)


_GEOMETRY_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_TANK_HEIGHT_CM, default=DEFAULT_TANK_HEIGHT_CM): vol.All(
            vol.Coerce(float), vol.Range(min=1.0, max=200.0)
        ),
        vol.Required(CONF_DEAD_ZONE_CM, default=DEFAULT_DEAD_ZONE_CM): vol.All(
            vol.Coerce(float), vol.Range(min=0.0, max=50.0)
        ),
        vol.Required(CONF_FULL_OFFSET_CM, default=DEFAULT_FULL_OFFSET_CM): vol.All(
            vol.Coerce(float), vol.Range(min=0.0, max=200.0)
        ),
    }
)


class StarTankConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a STAR-Tank config flow."""

    VERSION = 1

    def __init__(self) -> None:
        self._discovered: BluetoothServiceInfoBleak | None = None
        self._discovered_addresses: dict[str, str] = {}

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> ConfigFlowResult:
        """Handle an advertisement forwarded by HA's bluetooth component."""
        if not _is_startank(discovery_info):
            return self.async_abort(reason="not_startank")
        await self.async_set_unique_id(discovery_info.address.upper())
        self._abort_if_unique_id_configured()
        self._discovered = discovery_info
        self.context["title_placeholders"] = {"name": self._title(discovery_info)}
        return await self.async_step_configure()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Let the user pick from live STAR-Tank advertisements."""
        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            await self.async_set_unique_id(address.upper())
            self._abort_if_unique_id_configured()
            service_info = next(
                (
                    si
                    for si in async_discovered_service_info(
                        self.hass, connectable=False
                    )
                    if si.address.upper() == address.upper()
                ),
                None,
            )
            self._discovered = service_info
            return await self.async_step_configure()

        current_ids = {entry.unique_id for entry in self._async_current_entries()}
        self._discovered_addresses = {
            si.address: self._title(si)
            for si in async_discovered_service_info(self.hass, connectable=False)
            if _is_startank(si) and si.address.upper() not in current_ids
        }
        if not self._discovered_addresses:
            return self.async_abort(reason="no_devices_found")

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {vol.Required(CONF_ADDRESS): vol.In(self._discovered_addresses)}
            ),
        )

    async def async_step_configure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for tank geometry, then create the entry."""
        assert self._discovered is not None
        if user_input is not None:
            return self.async_create_entry(
                title=self._title(self._discovered),
                data={CONF_ADDRESS: self._discovered.address.upper()},
                options=user_input,
            )
        return self.async_show_form(
            step_id="configure",
            data_schema=_GEOMETRY_SCHEMA,
            description_placeholders={"name": self._title(self._discovered)},
        )

    @staticmethod
    def _title(service_info: BluetoothServiceInfoBleak) -> str:
        tail = service_info.address.replace(":", "")[-6:].upper()
        return f"STAR-Tank {tail}"

    @staticmethod
    @callback
    def async_get_options_flow(config_entry) -> OptionsFlow:
        """Return the options flow."""
        return StarTankOptionsFlow()


class StarTankOptionsFlow(OptionsFlow):
    """Edit tank geometry after setup."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        current = self.config_entry.options
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_TANK_HEIGHT_CM,
                    default=current.get(CONF_TANK_HEIGHT_CM, DEFAULT_TANK_HEIGHT_CM),
                ): vol.All(vol.Coerce(float), vol.Range(min=1.0, max=200.0)),
                vol.Required(
                    CONF_DEAD_ZONE_CM,
                    default=current.get(CONF_DEAD_ZONE_CM, DEFAULT_DEAD_ZONE_CM),
                ): vol.All(vol.Coerce(float), vol.Range(min=0.0, max=50.0)),
                vol.Required(
                    CONF_FULL_OFFSET_CM,
                    default=current.get(CONF_FULL_OFFSET_CM, DEFAULT_FULL_OFFSET_CM),
                ): vol.All(vol.Coerce(float), vol.Range(min=0.0, max=200.0)),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
