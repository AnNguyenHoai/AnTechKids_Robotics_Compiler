# runtime/sensors/light_sensor.py
from .base import ISensor
from .sensor_value import SensorValue
from ..hardware.interface import IHardware

class LightSensor(ISensor):
    """Light sensor (brightness)."""

    def __init__(self, hardware: IHardware, channel: int, name: str = "light"):
        self._hardware = hardware
        self._channel = channel
        self._name = name
        self._last_value = SensorValue(raw=0, normalized=0.0)

    @property
    def name(self) -> str:
        return f"{self._name}_{self._channel}"

    @property
    def event_handler(self):
        return None  # not implemented

    @event_handler.setter
    def event_handler(self, handler):
        pass

    def initialize(self) -> None:
        pass

    def update(self) -> None:
        # Assuming hardware read_line_sensor can be used for light (analog)
        raw = self._hardware.read_line_sensor(self._channel)
        # Normalize: 0-1023 to 0.0-1.0
        normalized = raw / 1023.0
        self._last_value = SensorValue(raw=raw, normalized=normalized)

    def read(self) -> SensorValue:
        return self._last_value

    def reset(self) -> None:
        self._last_value = SensorValue(raw=0, normalized=0.0)

    def health(self) -> str:
        return "healthy"

    def shutdown(self) -> None:
        pass

    # High-level
    def brightness(self) -> float:
        return float(self._last_value.raw)

    def normalized(self) -> float:
        return self._last_value.normalized