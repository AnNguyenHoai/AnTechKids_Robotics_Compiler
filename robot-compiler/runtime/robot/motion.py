# runtime/robot/motion.py
from typing import Optional
from .state import RobotState
from .events import RobotEvent, EventType
from ..hardware.interface import IHardware
from ..value import IntegerValue

class MotionController:
    def __init__(self, hardware: IHardware):
        self.hardware = hardware
        self.state = RobotState.IDLE
        self.current_direction = None
        self.current_speed = 0
        self.events = []

    def _emit(self, event_type: EventType, data=None):
        self.events.append(RobotEvent(event_type, data))

    def forward(self, speed: int):
        self._validate_speed(speed)
        self.current_direction = "forward"
        self.current_speed = speed
        self.state = RobotState.MOVING
        self.hardware.set_motor(speed, speed)
        self._emit(EventType.MOVEMENT_STARTED, {"direction": "forward", "speed": speed})

    def backward(self, speed: int):
        self._validate_speed(speed)
        self.current_direction = "backward"
        self.current_speed = speed
        self.state = RobotState.MOVING
        self.hardware.set_motor(-speed, -speed)
        self._emit(EventType.MOVEMENT_STARTED, {"direction": "backward", "speed": speed})

    def left(self, speed: int):
        self._validate_speed(speed)
        self.current_direction = "left"
        self.current_speed = speed
        self.state = RobotState.TURNING
        self.hardware.set_motor(-speed, speed)
        self._emit(EventType.MOVEMENT_STARTED, {"direction": "left", "speed": speed})

    def right(self, speed: int):
        self._validate_speed(speed)
        self.current_direction = "right"
        self.current_speed = speed
        self.state = RobotState.TURNING
        self.hardware.set_motor(speed, -speed)
        self._emit(EventType.MOVEMENT_STARTED, {"direction": "right", "speed": speed})

    def stop(self):
        self.hardware.set_motor(0, 0)
        self.state = RobotState.STOPPED
        self._emit(EventType.MOVEMENT_STOPPED)

    def wait(self, ms: int):
        self.state = RobotState.WAITING
        self.hardware.delay(ms)
        self.state = RobotState.IDLE

    def _validate_speed(self, speed: int):
        if speed < 0 or speed > 100:
            raise ValueError(f"Speed must be between 0 and 100, got {speed}")

    def get_state(self) -> RobotState:
        return self.state

    def get_events(self):
        return self.events

    def clear_events(self):
        self.events.clear()