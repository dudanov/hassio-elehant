"""Support for Elehant sensors."""

import dataclasses as dc
import itertools as it
import logging

from homeassistant.components.bluetooth.passive_update_processor import (
    PassiveBluetoothDataProcessor,
    PassiveBluetoothDataUpdate,
    PassiveBluetoothEntityKey,
    PassiveBluetoothProcessorEntity,
)
from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.components.sensor.const import SensorDeviceClass, SensorStateClass
from homeassistant.const import (
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    EntityCategory,
    UnitOfEnergy,
    UnitOfTemperature,
    UnitOfVolume,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import ElehantConfigEntry
from .const import DOMAIN
from .elehant import ElehantData
from .translate import ElehantI18n

_LOGGER = logging.getLogger(__name__)

_COMMON_SENSORS = [
    SensorEntityDescription(
        device_class=SensorDeviceClass.TEMPERATURE,
        key="temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        device_class=SensorDeviceClass.BATTERY,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:battery-bluetooth-variant",
        key="battery",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:bluetooth",
        key="rssi",
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        icon="mdi:send-clock",
        key="timestamp",
        translation_key="last_report",
    ),
]


def _values_descriptions(data: ElehantData):
    _class, unit = SensorDeviceClass.ENERGY, UnitOfVolume.CUBIC_METERS

    match data.type:
        case 1:
            _class = SensorDeviceClass.GAS
        case 2:
            _class = SensorDeviceClass.WATER
        case 3:
            unit = UnitOfEnergy.KILO_WATT_HOUR
        case 4:
            unit = UnitOfEnergy.GIGA_CALORIE

    _VALUE_SENSOR = SensorEntityDescription(
        key="value_1",
        device_class=_class,
        native_unit_of_measurement=unit,
        state_class=SensorStateClass.TOTAL,
    )

    result = [_VALUE_SENSOR]

    if data.value_2 is not None:
        result.append(dc.replace(_VALUE_SENSOR, key="value_2"))

    return result


def sensor_update_to_bluetooth_data_update(
    input: tuple[ElehantData, ElehantI18n],
) -> PassiveBluetoothDataUpdate:
    """Convert a sensor update to a Bluetooth data update."""

    data, i18n = input
    _value_sensors = _values_descriptions(data)

    def _it():
        return it.chain(_COMMON_SENSORS, _value_sensors)

    device_info = dr.DeviceInfo(
        connections={(dr.CONNECTION_BLUETOOTH, data.address)},
        identifiers={(DOMAIN, data.unique_id)},
        serial_number=data.str_serial,
        sw_version=data.sw_version,
        **i18n._asdict(),
    )

    result = PassiveBluetoothDataUpdate(
        devices={data.address: device_info},
        entity_descriptions={
            PassiveBluetoothEntityKey(x.key, data.address): x for x in _it()
        },
        entity_data={
            PassiveBluetoothEntityKey(x.key, data.address): getattr(data, x.key)
            for x in _it()
        },
    )

    return result


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ElehantConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Elehant sensors."""

    coordinator = entry.runtime_data

    processor = PassiveBluetoothDataProcessor(sensor_update_to_bluetooth_data_update)

    entry.async_on_unload(
        processor.async_add_entities_listener(
            ElehantBluetoothSensorEntity, async_add_entities
        )
    )

    entry.async_on_unload(coordinator.async_register_processor(processor))


class ElehantBluetoothSensorEntity(
    PassiveBluetoothProcessorEntity[
        PassiveBluetoothDataProcessor[int | float, tuple[ElehantData, ElehantI18n]]
    ],
    SensorEntity,
):
    @property
    def available(self) -> bool:
        """Return whether the entity was available in the last update."""

        return (
            super().available
            and self.processor.entity_data.get(self.entity_key) is not None
        )

    @property
    def native_value(self) -> int | float | None:
        """Return the native value."""

        return self.processor.entity_data.get(self.entity_key)
