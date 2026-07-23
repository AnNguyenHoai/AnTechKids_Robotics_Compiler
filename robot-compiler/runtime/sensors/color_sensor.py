# runtime/sensors/color_sensor.py
from .base import ISensor
from .sensor_value import SensorValue
from ..hardware.interface import IHardware
from typing import Tuple

class ColorSensor(ISensor):
    """Color sensor (RGB) - placeholder."""

    def __init__(self, hardware: IHardware, name: str = "color"):
        self._hardware = hardware
        self._name = name
        self._last_value = SensorValue(raw=(0,0,0), normalized=(0.0,0.0,0.0))
        self._event_handler = None

    @property
    def name(self) -> str:
        return self._name

    @property
    def event_handler(self):
        return self._event_handler

    @event_handler.setter
    def event_handler(self, handler):
        self._event_handler = handler

    def initialize(self) -> None:
        pass

    def update(self) -> None:
        # Placeholder: read RGB from hardware (not implemented in IHardware)
        # For now, mock values
        raw = (0, 0, 0)
        normalized = (0.0, 0.0, 0.0)
        self._last_value = SensorValue(raw=raw, normalized=normalized)

    def read(self) -> SensorValue:
        return self._last_value

    def reset(self) -> None:
        self._last_value = SensorValue(raw=(0,0,0), normalized=(0.0,0.0,0.0))

    def health(self) -> str:
        return "healthy"

    def shutdown(self) -> None:
        pass

    # High-level
    def color(self) -> Tuple[int, int, int]:
        return self._last_value.raw

    def rgb(self) -> Tuple[float, float, float]:
        return self._last_value.normalized

    def confidence(self) -> float:
        return self._last_value.quality