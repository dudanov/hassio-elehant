import dataclasses as dc
import datetime as dt

from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData


class ElehantError(Exception):
    pass


class NotElehantDeviceError(ElehantError):
    pass


class UnknownPacketError(ElehantError):
    pass


class UnknownDeviceError(ElehantError):
    pass


@dc.dataclass(frozen=True)
class ElehantData:
    """Данные прибора учета Элехант, получаемые из рекламного пакета BLE"""

    type: int
    """Код типа"""
    kind: int
    """Код модели"""
    number: int
    """Серийный номер"""
    sw_version: str
    """Версия прошивки"""
    address: str
    """Адрес"""
    rssi: int
    """Уровень сигнала RSSI"""
    timestamp: dt.datetime
    """Штамп времени"""

    _: dc.KW_ONLY

    battery: int
    """Уровень заряда батареи"""
    temperature: float
    """Температура среды"""
    value_1: float
    """Показание 1"""
    value_2: float | None = None
    """Показание 2"""

    @classmethod
    def from_ble(cls, dev: BLEDevice, adv: AdvertisementData):
        x = dev.address.replace(":", "").lower()

        if len(x) != 12 or not x.startswith("b0"):
            raise NotElehantDeviceError(
                "Bluetooth device hasn't valid Elehant address."
            )

        # type, model, serial
        sign = int(x[4:6], 16), int(x[2:4], 16), int(x[6:], 16)

        if not (x := adv.manufacturer_data.get(65535)) or len(x) != 17 or x[0] != 0x80:
            raise NotElehantDeviceError(
                "Advertisement data hasn't valid manufacturer data."
            )

        if sign != (x[4], x[5], int.from_bytes(x[6:9], "little")):
            raise NotElehantDeviceError(
                "Device signatures in address and adverisement data aren't equals."
            )

        sw_version, packet_version = "{}.{}".format(*divmod(x[16], 10)), x[3]

        # type, model, serial, sw_version, address, rssi, timestamp
        args = *sign, sw_version, dev.address, adv.rssi, dt.datetime.now(dt.UTC)

        if packet_version == 0x01:
            return cls(
                *args,
                battery=min(x[13], 100),
                temperature=int.from_bytes(x[14:16], "little") / 1e2,
                value_1=int.from_bytes(x[9:13], "little") / 1e4,
            )

        if packet_version == 0x05:
            # Значения показаний 28-битные
            v1, v2 = map(lambda x: x << 24, divmod(x[9], 16))
            v1 += int.from_bytes(x[10:13], "big")
            v2 += int.from_bytes(x[13:16], "big")

            return cls(
                *args,
                battery=min(x[1], 100),
                temperature=x[2],
                value_1=v1 / 1e3,
                value_2=v2 / 1e3,
            )

        raise UnknownPacketError("Unknown v%d packet", packet_version)

    @property
    def model_key(self) -> str:
        """Строковый ключ словаря модели"""
        return f"{self.type}-{self.kind}"

    @property
    def serial_number(self) -> str:
        """Серийный номер в виде строки"""
        return f"{self.number:07}"

    @property
    def unique_id(self) -> str:
        """Уникальный идентификатор"""
        return f"{self.model_key}-{self.serial_number}"
