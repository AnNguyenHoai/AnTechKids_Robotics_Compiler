"""
AUTO GENERATED FILE
"""

from compiler.handlers.motion_handler import MotionHandler
from compiler.handlers.system_handler import SystemHandler

FUNCTION_REGISTRY = {
    "forward": {
        "handler": MotionHandler.forward,
        "opcode": "Forward",
        "arguments": 1,
        "category": "system",
        "description": "Move robot forward"
    },
    "backward": {
        "handler": MotionHandler.backward,
        "opcode": "Backward",
        "arguments": 1,
        "category": "system",
        "description": "Move robot backward"
    },
    "turn_left": {
        "handler": MotionHandler.turn_left,
        "opcode": "TurnLeft",
        "arguments": 1,
        "category": "system",
        "description": "Rotate robot left"
    },
    "turn_right": {
        "handler": MotionHandler.turn_right,
        "opcode": "TurnRight",
        "arguments": 1,
        "category": "system",
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
}
