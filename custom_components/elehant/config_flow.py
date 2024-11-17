"""Config flow for Elehant integration."""

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
)
from homeassistant.const import CONF_UNIQUE_ID
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN
from .elehant import ElehantData, ElehantError
from .helpers import get_device_name

_LOGGER = logging.getLogger(__name__)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Elehant."""

    _discovered_device: ElehantData | None
    _discovered_devices: dict[str, ElehantData]

    def __init__(self) -> None:
        """Set up a new config flow for Elehant."""
        self._discovered_device = None
        self._discovered_devices = {}

    async def async_step_bluetooth(self, info: BluetoothServiceInfoBleak) -> FlowResult:
        """Handle the Bluetooth discovery step."""

        try:
            device = ElehantData.from_ble(info.device, info.advertisement)

        except ElehantError:
            return self.async_abort(reason="not_supported")

        await self.async_set_unique_id(info.address)
        self._abort_if_unique_id_configured()
        self._discovered_device = device

        return await self.async_step_bluetooth_confirm()

    async def async_step_bluetooth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm discovery."""
        assert (device := self._discovered_device)

        if user_input is not None:
            return self.async_create_entry(title=self._name, data={})

        self._name = await get_device_name(self.hass, device)
        self.context["title_placeholders"] = {"name": self._name}
        self._set_confirm_only()

        return self.async_show_form(step_id="bluetooth_confirm")

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the user step to pick discovered device."""
        if user_input is not None:
            unique_id = user_input[CONF_UNIQUE_ID]
            device = self._discovered_devices[unique_id]

            await self.async_set_unique_id(device.address, raise_on_progress=False)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=await get_device_name(self.hass, device), data={}
            )

        current_ids = self._async_current_ids()

        for info in async_discovered_service_info(self.hass, False):
            if info.address in current_ids:
                continue

            try:
                device = ElehantData.from_ble(info.device, info.advertisement)

            except ElehantError:
                continue

            self._discovered_devices[device.unique_id] = device

        if not self._discovered_devices:
            return self.async_abort(reason="no_devices_found")

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_UNIQUE_ID): vol.In(
                        {
                            k: await get_device_name(self.hass, v)
                            for k, v in self._discovered_devices.items()
                        }
                    )
                }
            ),
        )
