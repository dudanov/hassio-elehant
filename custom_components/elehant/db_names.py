from typing import NamedTuple

from homeassistant.core import HomeAssistant

from .elehant import ElehantData


class ElehantNames(NamedTuple):
    manufacturer: str
    model: str
    name: str


_TYPES_EN = {
    "1": "Gas meter",
    "2": "Water meter",
    "3": "Electricity meter",
    "4": "Heat meter",
}

_TYPES_RU = {
    "1": "Счетчик газа",
    "2": "Счетчик воды",
    "3": "Счетчик электричества",
    "4": "Счетчик тепла",
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


def get_translated_names(hass: HomeAssistant, dev: ElehantData):
    if hass.config.language == "ru":
        manufacturer = "Элехант"
        type = _TYPES_RU[dev.key_type]
        model = _MODELS_RU[dev.key_model]

    else:
        manufacturer = "Elehant"
        type = _TYPES_EN[dev.key_type]
        model = _MODELS_EN[dev.key_model]

    return ElehantNames(
        manufacturer=manufacturer,
        model=f"{type} {model}",
        name=f"{type} {model}-{dev.str_serial}",
    )