# compiler/isa/opcode.py
from enum import Enum, auto

class RobotOpcode(Enum):
    # Movement
    MOVE_RUN = auto()
    MOVE_RUN_TIME = auto()
    MOVE_STOP = auto()

    # Timing
    WAIT = auto()

    # Control Flow
    JUMP = auto()
    JUMP_IF = auto()

    # Function
    CALL = auto()
    RETURN = auto()

    # Servo
    SERVO_MOVE = auto()

    # Sensor
    READ_TRACE = auto()

    # Thread
    THREAD_START = auto()
    THREAD_END = auto()