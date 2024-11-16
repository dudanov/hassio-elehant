import logging

from homeassistant.components.bluetooth import (
    BluetoothScanningMode,
    async_rediscover_address,
)
from homeassistant.components.bluetooth.passive_update_processor import (
    PassiveBluetoothProcessorCoordinator,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .elehant import ElehantData

PLATFORMS: list[Platform] = [Platform.SENSOR]

_LOGGER = logging.getLogger(__name__)

type ElehantConfigEntry = ConfigEntry[PassiveBluetoothProcessorCoordinator[ElehantData]]


async def async_setup_entry(hass: HomeAssistant, entry: ElehantConfigEntry) -> bool:
    """Set up Elehant from a config entry."""

    assert (address := entry.unique_id)

    entry.runtime_data = PassiveBluetoothProcessorCoordinator(
        hass,
        _LOGGER,
        address=address,
        mode=BluetoothScanningMode.PASSIVE,
        update_method=lambda x: ElehantData.from_ble(x.device, x.advertisement),
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.runtime_data.async_start())

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""

    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        assert (address := entry.unique_id)
        async_rediscover_address(hass, address)

    return unload_ok
