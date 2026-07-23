# runtime/sensors/ultrasonic_sensor.py
from .base import ISensor
from .sensor_value import SensorValue
from ..hardware.interface import IHardware

class UltrasonicSensor(ISensor):
    """Ultrasonic sensor runtime: distance, obstacle detection."""

    def __init__(self, hardware: IHardware, name: str = "ultrasonic"):
        self._hardware = hardware
        self._name = name
        self._last_value = SensorValue(raw=0, normalized=0.0)
        self._event_handler = None
        self._threshold = 20.0  # cm

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
        raw = self._hardware.read_ultrasonic()
        # Normalize: assume range 0-100 cm, map to 0.0-1.0
        normalized = max(0.0, min(1.0, raw / 100.0))
        self._last_value = SensorValue(raw=raw, normalized=normalized)

    def read(self) -> SensorValue:
        return self._last_value

    def reset(self) -> None:
        self._last_value = SensorValue(raw=0, normalized=0.0)

    def health(self) -> str:
        if self._last_value.valid:
            return "healthy"
        return "invalid"

    def shutdown(self) -> None:
        pass

    # High-level methods
    def distance(self) -> float:
        return float(self._last_value.raw)

    def has_obstacle(self, threshold: float = None) -> bool:
        if threshold is None:
            threshold = self._threshold
        return self.distance() < threshold