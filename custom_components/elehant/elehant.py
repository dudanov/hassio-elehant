import dataclasses as dc
import datetime as dt

from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData


class ElehantError(Exception):
    pass


class NotElehantDevice(ElehantError):
    pass


class UnsupportedPacket(ElehantError):
    pass


@dc.dataclass(frozen=True)
class ElehantData:
    """Данные прибора учета Элехант, получаемые из рекламного пакета BLE"""

    type: int
    """Код типа"""
    model: int
    """Код модели"""
    serial: int
    """Серийный номер"""

    _: dc.KW_ONLY

    sw_version: str
    """Версия прошивки"""
    battery: int
    """Уровень заряда батареи"""
    temperature: float
    """Температура среды"""
    value_1: float
    """Показание 1"""
    value_2: float | None = None
    """Показание 2"""
    address: str
    """Адрес"""
    rssi: int
    """Уровень сигнала RSSI"""

    @classmethod
    def from_ble(cls, dev: BLEDevice, adv: AdvertisementData):
        x = dev.address.replace(":", "").lower()

        if len(x) != 12 or not x.startswith("b0"):
            raise NotElehantDevice("Bluetooth device hasn't valid Elehant address.")

        # (type, model, serial)
        sign = int(x[4:6], 16), int(x[2:4], 16), int(x[6:], 16)

        if not (x := adv.manufacturer_data.get(65535)) or len(x) != 17 or x[0] != 0x80:
            raise NotElehantDevice("Advertisement data hasn't valid manufacturer data.")

        if sign != (x[4], x[5], int.from_bytes(x[6:9], "little")):
            raise NotElehantDevice(
                "Device signatures in address and adverisement data aren't equals."
            )

        sw_version, packet_version = "{}.{}".format(*divmod(x[16], 10)), x[3]

        if packet_version == 0x01:
            return cls(
                *sign,
                sw_version=sw_version,
                battery=min(x[13], 100),
                temperature=int.from_bytes(x[14:16], "little") / 1e2,
                value_1=int.from_bytes(x[9:13], "little") / 1e4,
                address=dev.address,
                rssi=adv.rssi,
            )

        if packet_version == 0x05:
            # Значения показаний 28-битные
            v1, v2 = map(lambda x: x << 24, divmod(x[9], 16))
            v1 += int.from_bytes(x[10:13], "big")
            v2 += int.from_bytes(x[13:16], "big")

            return cls(
                *sign,
                sw_version=sw_version,
                battery=min(x[1], 100),
                temperature=x[2],
                value_1=v1 / 1e3,
                value_2=v2 / 1e3,
                address=dev.address,
                rssi=adv.rssi,
            )

        raise UnsupportedPacket("Packet version %d is not supported.", packet_version)

    @property
    def key_type(self) -> str:
        """Строковый ключ словаря типа"""
        return f"{self.type}"

    @property
    def key_model(self) -> str:
        """Строковый ключ словаря модели"""
        return f"{self.type}-{self.model}"

    @property
    def str_serial(self) -> str:
        """Серийный номер в виде строки"""
        return f"{self.serial:07}"

    @property
    def unique_id(self) -> str:
        """Уникальный идентификатор"""
        return f"{self.key_model}-{self.str_serial}"

    @property
    def last_report(self) -> dt.datetime:
        """Возвращает текущий штамп времени"""
        return dt.datetime.now(dt.UTC)
