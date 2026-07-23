# runtime/sensors/line_sensor.py
from .base import ISensor
from .sensor_value import SensorValue
from .sensor_event import SensorEvent, SensorEventType
from ..hardware.interface import IHardware
import time

class LineSensor(ISensor):
    """Line sensor runtime: reads raw values, normalizes, provides high-level info."""

    def __init__(self, hardware: IHardware, channel: int, name: str = "line"):
        self._hardware = hardware
        self._channel = channel
        self._name = name
        self._last_value = SensorValue(raw=0, normalized=0.0)
        self._event_handler = None

    @property
    def name(self) -> str:
        return f"{self._name}_{self._channel}"

    @property
    def event_handler(self):
        return self._event_handler

    @event_handler.setter
    def event_handler(self, handler):
        self._event_handler = handler

    def initialize(self) -> None:
        # No specific initialization needed for mock/adapters
        pass

    def update(self) -> None:
        raw = self._hardware.read_line_sensor(self._channel)
        # Normalize: assume 0-1023, map to 0.0-1.0
        normalized = raw / 1023.0
        self._last_value = SensorValue(raw=raw, normalized=normalized)

    def read(self) -> SensorValue:
        return self._last_value

    def reset(self) -> None:
        self._last_value = SensorValue(raw=0, normalized=0.0)

    def health(self) -> str:
        # Simple health check: if last reading is valid
        if self._last_value.valid:
            return "healthy"
        return "invalid"

    def shutdown(self) -> None:
        pass

    # High-level methods
    def is_on_line(self, threshold: float = 0.5) -> bool:
        """Return True if sensor is over a dark line (assuming normalized < threshold)."""
        return self._last_value.normalized < threshold

    def position(self) -> float:
        """Return normalized position (0.0 to 1.0)."""
        return self._last_value.normalized

    def confidence(self) -> float:
        """Return confidence based on quality."""
        return self._last_value.quality