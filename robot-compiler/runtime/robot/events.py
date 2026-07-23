# runtime/robot/events.py
from dataclasses import dataclass
from enum import Enum
from typing import Any

class EventType(Enum):
    MOVEMENT_STARTED = "movement_started"
    MOVEMENT_STOPPED = "movement_stopped"
    SENSOR_CHANGED = "sensor_changed"
    EXECUTION_FINISHED = "execution_finished"
    ERROR = "error"

@dataclass
class RobotEvent:
    type: EventType
    data: Any = None