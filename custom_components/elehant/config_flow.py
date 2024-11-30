"""Config flow for Elehant integration."""

import logging
from typing import Any

import voluptuous as vol
from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
)
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_ADDRESS

from .const import DOMAIN
from .elehant import ElehantData, ElehantError
from .translate import get_i18n

_LOGGER = logging.getLogger(__name__)


class ElehantConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Elehant."""

    _device: str
    _devices: dict[str, str]

    async def async_step_bluetooth(
        self, info: BluetoothServiceInfoBleak
    ) -> ConfigFlowResult:
        """Handle the Bluetooth discovery step."""

        try:
            device = ElehantData.from_ble(info.device, info.advertisement)
            self._device = get_i18n(self.hass, device).name

        except ElehantError:
            return self.async_abort(reason="not_supported")

        await self.async_set_unique_id(info.address)
        self._abort_if_unique_id_configured()

        return await self.async_step_bluetooth_confirm()

    async def async_step_bluetooth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm discovery."""

        if user_input is not None:
            return self.async_create_entry(title=self._device, data={})

        self.context["title_placeholders"] = {"name": self._device}
        self._set_confirm_only()

        return self.async_show_form(step_id="bluetooth_confirm")

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the user step to pick discovered device."""

        if user_input is not None:
            address = user_input[CONF_ADDRESS]

            await self.async_set_unique_id(address, raise_on_progress=False)
            self._abort_if_unique_id_configured()

            name = self._devices[address]
            return self.async_create_entry(title=name, data={})

        self._devices = {}
        current_ids = self._async_current_ids()

        for info in async_discovered_service_info(self.hass, False):
            if info.address in current_ids:
                continue

            try:
                device = ElehantData.from_ble(info.device, info.advertisement)
                self._devices[info.address] = get_i18n(self.hass, device).name

            except ElehantError:
                continue

        if not self._devices:
            return self.async_abort(reason="no_devices_found")

        schema = vol.Schema({vol.Required(CONF_ADDRESS): vol.In(self._devices)})

        return self.async_show_form(step_id="user", data_schema=schema)
