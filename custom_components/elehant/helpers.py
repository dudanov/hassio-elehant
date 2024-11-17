from homeassistant.core import HomeAssistant
from homeassistant.helpers import translation as i18n

from .const import DOMAIN
from .elehant import ElehantData


async def get_translated_key(
    hass: HomeAssistant,
    category: str,
    key: str,
    placeholders: dict[str, str] | None = None,
    fallback: str | None = None,
):
    language = hass.config.language
    tr = await i18n.async_get_translations(hass, language, category, [DOMAIN])

    return tr.get(f"component.{DOMAIN}.{category}.{key}", fallback or "").format(
        **placeholders or {}
    )


def get_device_name(hass: HomeAssistant, device: ElehantData):
    return get_translated_key(
        hass,
        "device",
        key=f"{device.key_model}.name",
        placeholders={"serial": device.str_serial},
    )
