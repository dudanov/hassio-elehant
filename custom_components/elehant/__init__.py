import logging

from homeassistant.components.bluetooth import (
    BluetoothScanningMode,
    BluetoothServiceInfoBleak,
    async_rediscover_address,
)
from homeassistant.components.bluetooth.passive_update_processor import (
    PassiveBluetoothProcessorCoordinator,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .elehant import ElehantData, ElehantError
from .translate import ElehantI18N, get_i18n

PLATFORMS: list[Platform] = [Platform.SENSOR]

_LOGGER = logging.getLogger(__name__)

type ElehantConfigEntry = ConfigEntry[
    PassiveBluetoothProcessorCoordinator[tuple[ElehantData, ElehantI18N]]
]


async def async_setup_entry(hass: HomeAssistant, entry: ElehantConfigEntry) -> bool:
    """Set up Elehant from a config entry."""

    assert (address := entry.unique_id)

    def _update(info: BluetoothServiceInfoBleak):
        try:
            data = ElehantData.from_ble(info.device, info.advertisement)
            i18n = get_i18n(hass, data)

        except ElehantError as exc:
            # Этого исключения быть не должно, так как счетчик проходил валидацию
            # на стадии визарда `ConfigFlow`. Все равно должен быть обработчик
            # на случай ошибки ПО счетчика.
            raise HomeAssistantError("Unexpected error") from exc

        return data, i18n

    entry.runtime_data = PassiveBluetoothProcessorCoordinator(
        hass,
        _LOGGER,
        address=address,
        mode=BluetoothScanningMode.PASSIVE,
        update_method=_update,
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.runtime_data.async_start())

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ElehantConfigEntry) -> bool:
    """Unload a config entry."""

    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        assert (address := entry.unique_id)
        async_rediscover_address(hass, address)

    return unload_ok
