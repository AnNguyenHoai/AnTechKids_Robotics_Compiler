# runtime/sensors/touch_sensor.py
from .base import ISensor
from .sensor_value import SensorValue
from .sensor_event import SensorEvent, SensorEventType
from ..hardware.interface import IHardware
import time

class TouchSensor(ISensor):
    """Touch sensor with debounce."""

    def __init__(self, hardware: IHardware, port: int, name: str = "touch", debounce_ms: int = 50):
        self._hardware = hardware
        self._port = port
        self._name = name
        self._debounce_ms = debounce_ms
        self._last_value = SensorValue(raw=False, normalized=0.0)
        self._last_state = False
        self._last_click_time = 0
        self._event_handler = None

    @property
    def name(self) -> str:
        return f"{self._name}_{self._port}"

    @property
    def event_handler(self):
        return self._event_handler

    @event_handler.setter
    def event_handler(self, handler):
        self._event_handler = handler

    def initialize(self) -> None:
        pass

    def update(self) -> None:
        raw = self._hardware.read_touch(self._port)
        # Normalize: bool to 0.0/1.0
        normalized = 1.0 if raw else 0.0
        new_val = SensorValue(raw=raw, normalized=normalized)
        # Debounce logic
        now = time.time() * 1000
        if raw != self._last_state:
            if now - self._last_click_time > self._debounce_ms:
                self._last_state = raw
                self._last_click_time = now
                if self._event_handler:
                    self._event_handler(SensorEvent(
                        sensor_name=self.name,
                        event_type=SensorEventType.CHANGED if raw else SensorEventType.DEACTIVATED,
                        value=raw
                    ))
        self._last_value = new_val

    def read(self) -> SensorValue:
        return self._last_value

    def reset(self) -> None:
        self._last_value = SensorValue(raw=False, normalized=0.0)
        self._last_state = False

    def health(self) -> str:
        return "healthy"  # simple

    def shutdown(self) -> None:
        pass

    # High-level methods
    def pressed(self) -> bool:
        return self._last_value.raw

    def released(self) -> bool:
        return not self.pressed()

    def clicked(self) -> bool:
        # For simplicity, just return if pressed (or implement edge detection)
        return self.pressed()