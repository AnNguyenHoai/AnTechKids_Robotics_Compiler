"""
AUTO GENERATED FILE
"""

from compiler.handlers.motion_handler import MotionHandler
from compiler.handlers.system_handler import SystemHandler
from compiler.handlers.sensor_handler import SensorHandler

FUNCTION_REGISTRY = {
    "forward": {
        "handler": MotionHandler.forward,
        "opcode": "Forward",
        "arguments": 1,
        "category": "motion",
        "description": "Move robot forward"
    },
    "backward": {
        "handler": MotionHandler.backward,
        "opcode": "Backward",
        "arguments": 1,
        "category": "motion",
        "description": "Move robot backward"
    },
    "turn_left": {
        "handler": MotionHandler.turn_left,
        "opcode": "TurnLeft",
        "arguments": 1,
        "category": "motion",
        "description": "Rotate robot left"
    },
    "turn_right": {
        "handler": MotionHandler.turn_right,
        "opcode": "TurnRight",
        "arguments": 1,
        "category": "motion",
        "description": "Rotate robot right"
    },
    "wait": {
        "handler": SystemHandler.wait,
        "opcode": "Wait",
        "arguments": 1,
        "category": "system",
        "description": "Wait milliseconds"
    },
    "stop": {
        "handler": SystemHandler.stop,
        "opcode": "Stop",
        "arguments": 0,
        "category": "system",
        "description": "Stop robot"
    },
    "read_ultrasonic": {
        "handler": SensorHandler.read_ultrasonic,
        "opcode": "ReadUltrasonic",
        "arguments": 0,
        "category": "sensor",
        "description": "Read ultrasonic distance in cm"
    },
    "read_touch": {
        "handler": SensorHandler.read_touch,
        "opcode": "ReadTouch",
        "arguments": 1,
        "category": "sensor",
        "description": "Read touch sensor state (0/1)"
    },
    "read_light": {
        "handler": SensorHandler.read_light,
        "opcode": "ReadLight",
        "arguments": 1,
        "category": "sensor",
        "description": "Read light sensor raw value (0-1023)"
    },
    "read_color": {
        "handler": SensorHandler.read_color,
        "opcode": "ReadColor",
        "arguments": 0,
        "category": "sensor",
        "description": "Read color sensor (placeholder)"
    },
    "read_line": {
        "handler": SensorHandler.read_line,
        "opcode": "ReadLine",
        "arguments": 1,
        "category": "sensor",
        "description": "Read line sensor (0=white, 1=dark)"
    },
}
