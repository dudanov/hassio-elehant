from typing import Mapping, NamedTuple

from homeassistant.core import HomeAssistant

from .elehant import ElehantData, UnknownDeviceError


class ElehantI18N(NamedTuple):
    manufacturer: str
    """Производитель"""
    model: str
    """Модель"""
    name: str
    """Полное имя"""


_TYPES_EN = {
    1: "Gas",
    2: "Water",
    3: "Electricity",
    4: "Heat",
}

_TYPES_RU = {
    1: "газа",
    2: "воды",
    3: "электроэнергии",
    4: "тепла",
}

_MODELS_EN = {
    "1-1": "DGM-1.8",
    "1-2": "DGM-3.2",
    "1-3": "DGM-4.0",
    "1-4": "DGM-6.0",
    "1-5": "DGM-1.6",
    "1-16": "GMDL-1.8",
    "1-17": "GMDL-3.2",
    "1-18": "GMDL-4.0",
    "1-19": "GMDL-6.0",
    "1-20": "GMDL-1.6",
    "1-32": "USGM-G1,6",
    "1-33": "USGM-G2,5",
    "1-34": "USGM-G4",
    "1-35": "USGM-G6",
    "1-36": "USGM-G10",
    "1-48": "GMDL-1.8TC",
    "1-49": "GMDL-3.2TC",
    "1-50": "GMDL-4.0TC",
    "1-51": "GMDL-6.0TC",
    "1-52": "GMDL-1.6TC",
    "1-64": "USGM-G1,6TC",
    "1-65": "USGM-G2,5TC",
    "1-66": "USGM-G4TC",
    "1-67": "USGM-G6TC",
    "1-68": "USGM-G10TC",
    "1-80": "DGM-1.8TC",
    "1-81": "DGM-3.2TC",
    "1-82": "DGM-4.0TC",
    "1-83": "DGM-6.0TC",
    "1-84": "DGM-1.6TC",
    "2-1": "DWM-15",
    "2-2": "DWM-20",
    "2-3": "DTM-15",
    "2-4": "DTM-15",
    "2-5": "DTM-20",
    "2-6": "DTM-20",
    "3-1": "DEM",
    "4-1": "DTM-10",
}

_MODELS_RU = {
    "1-1": "СГБ-1.8",
    "1-2": "СГБ-3.2",
    "1-3": "СГБ-4.0",
    "1-4": "СГБ-6.0",
    "1-5": "СГБ-1.6",
    "1-16": "СГБД-1.8",
    "1-17": "СГБД-3.2",
    "1-18": "СГБД-4.0",
    "1-19": "СГБД-6.0",
    "1-20": "СГБД-1.6",
    "1-32": "СОНИК-G1,6",
    "1-33": "СОНИК-G2,5",
    "1-34": "СОНИК-G4",
    "1-35": "СОНИК-G6",
    "1-36": "СОНИК-G10",
    "1-48": "СГБД-1.8ТК",
    "1-49": "СГБД-3.2ТК",
    "1-50": "СГБД-4.0ТК",
    "1-51": "СГБД-6.0ТК",
    "1-52": "СГБД-1.6ТК",
    "1-64": "СОНИК-G1,6ТК",
    "1-65": "СОНИК-G2,5ТК",
    "1-66": "СОНИК-G4ТК",
    "1-67": "СОНИК-G6ТК",
    "1-68": "СОНИК-G10ТК",
    "1-80": "СГБ-1.8ТК",
    "1-81": "СГБ-3.2ТК",
    "1-82": "СГБ-4.0ТК",
    "1-83": "СГБ-6.0ТК",
    "1-84": "СГБ-1.6ТК",
    "2-1": "СВД-15",
    "2-2": "СВД-20",
    "2-3": "СВТ-15",
    "2-4": "СВТ-15",
    "2-5": "СВТ-20",
    "2-6": "СВТ-20",
    "3-1": "СЭБ",
    "4-1": "СТБ-10",
}


def _keys_assertion(first: Mapping, *others: Mapping):
    keys = first.keys()
    assert all(keys == x.keys() for x in others)


# Ключи языковых словарей должны совпадать
_keys_assertion(_TYPES_EN, _TYPES_RU)
_keys_assertion(_MODELS_EN, _MODELS_RU)


def get_i18n(hass: HomeAssistant, dev: ElehantData) -> ElehantI18N:
    """Предоставляет перевод"""

    try:
        if hass.config.language == "ru":
            manufacturer = "Элехант"
            type = f"Счетчик {_TYPES_RU[dev.type]}"
            model = _MODELS_RU[dev.model_key]

        else:
            manufacturer = "Elehant"
            type = f"{_TYPES_EN[dev.type]} meter"
            model = _MODELS_EN[dev.model_key]

    except KeyError:
        raise UnknownDeviceError("Unknown %s device", dev.model_key)

    model = f"{type} {model}"
    name = f"{model}-{dev.serial_number}"

    return ElehantI18N(manufacturer, model, name)
