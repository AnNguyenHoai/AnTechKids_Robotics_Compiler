# runtime/robot/state.py
from enum import Enum

class RobotState(Enum):
    IDLE = "idle"
    MOVING = "moving"
    TURNING = "turning"
    WAITING = "waiting"
    STOPPED = "stopped"
    ERROR = "error"