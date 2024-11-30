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
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import ElehantConfigEntry
from .elehant import ElehantData

_LOGGER = logging.getLogger(__name__)

_COMMON_SENSORS = (
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
        icon="mdi:bluetooth-audio",
        key="timestamp",
        translation_key="last_report",
    ),
)


def _values_descriptions(data: ElehantData):
    cls, unit = SensorDeviceClass.ENERGY, UnitOfVolume.CUBIC_METERS

    match data.type:
        case 1:
            cls = SensorDeviceClass.GAS
        case 2:
            cls = SensorDeviceClass.WATER
        case 3:
            unit = UnitOfEnergy.KILO_WATT_HOUR
        case 4:
            unit = UnitOfEnergy.GIGA_CALORIE

    _SENSOR = SensorEntityDescription(
        key="value_1",
        device_class=cls,
        native_unit_of_measurement=unit,
        state_class=SensorStateClass.TOTAL,
    )

    sensors = [_SENSOR]

    if data.value_2 is not None:
        sensors.append(dc.replace(_SENSOR, key="value_2"))

    return tuple(sensors)


def sensor_update_to_bluetooth_data_update(
    input: tuple[ElehantData, DeviceInfo],
) -> PassiveBluetoothDataUpdate:
    """Convert a sensor update to a Bluetooth data update."""

    data, device_info = input
    _VALUES_SENSORS = _values_descriptions(data)

    def _it():
        return it.chain(_COMMON_SENSORS, _VALUES_SENSORS)

    return PassiveBluetoothDataUpdate(
        devices={None: device_info},
        entity_descriptions={PassiveBluetoothEntityKey(x.key, None): x for x in _it()},
        entity_data={
            PassiveBluetoothEntityKey(x.key, None): getattr(data, x.key) for x in _it()
        },
    )


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
        PassiveBluetoothDataProcessor[int | float, tuple[ElehantData, DeviceInfo]]
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
