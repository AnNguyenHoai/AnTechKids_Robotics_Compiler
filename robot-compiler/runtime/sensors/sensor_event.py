# runtime/sensors/sensor_event.py
from enum import Enum, auto
from dataclasses import dataclass
from typing import Any

class SensorEventType(Enum):
    ACTIVATED = auto()
    DEACTIVATED = auto()
    CHANGED = auto()
    ERROR = auto()
    DISCONNECTED = auto()

@dataclass
class SensorEvent:
    """Event emitted by a sensor."""
    sensor_name: str
    event_type: SensorEventType
    value: Any = None
    message: str = ""