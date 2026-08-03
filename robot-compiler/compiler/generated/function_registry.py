"""
AUTO GENERATED FILE
"""

from compiler.handlers.motion_handler import MotionHandler
from compiler.handlers.system_handler import SystemHandler
from compiler.handlers.sensor_handler import SensorHandler
from compiler.handlers.servo_handler import ServoHandler
from compiler.handlers.led_handler import LedHandler
from compiler.handlers.motor_handler import MotorHandler
from compiler.handlers.line_handler import LineHandler
from compiler.handlers.peripheral_handler import PeripheralHandler

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
    "set_motor_speed": {
        "handler": MotionHandler.set_motor_speed,
        "opcode": "SetMotorSpeed",
        "arguments": 2,
        "category": "motion",
        "description": "Set motor speeds independently"
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
    "get_trace_value": {
        "handler": SensorHandler.get_trace_value,
        "opcode": "GetTraceValue",
        "arguments": 2,
        "category": "sensor",
        "description": "Get trace sensor value (0/50/100 based on line detection)"
    },
    "get_trace_state": {
        "handler": SensorHandler.get_trace_state,
        "opcode": "GetTraceState",
        "arguments": 2,
        "category": "sensor",
        "description": "Get trace sensor state (boolean)"
    },
    "get_trace_raw": {
        "handler": SensorHandler.get_trace_raw,
        "opcode": "GetTraceRaw",
        "arguments": 1,
        "category": "sensor",
        "description": "Get raw bitmask of all 3 trace sensors"
    },
    "set_servo": {
        "handler": ServoHandler.set_servo,
        "opcode": "SetServo",
        "arguments": 2,
        "category": "servo",
        "description": "Set servo angle"
    },
    "set_3c_led": {
        "handler": LedHandler.set_3c_led,
        "opcode": "Set3CLed",
        "arguments": 2,
        "category": "led",
        "description": "Set 3-color LED state"
    },
    "set_light_sensor_led": {
        "handler": LedHandler.set_light_sensor_led,
        "opcode": "SetLightSensorLed",
        "arguments": 2,
        "category": "led",
        "description": "Set light sensor LED state"
    },
    "set_motor_straight_angle": {
        "handler": MotorHandler.set_motor_straight_angle,
        "opcode": "SetMotorStraightAngle",
        "arguments": 4,
        "category": "motor",
        "description": "Set motor straight angle"
    },
    "line_basis": {
        "handler": LineHandler.line_basis,
        "opcode": "LineBasis",
        "arguments": 1,
        "category": "line",
        "description": "Basic line following step (adjust motors based on sensor mask)"
    },
    "line_follow": {
        "handler": LineHandler.line_follow,
        "opcode": "LineFollow",
        "arguments": 1,
        "category": "line",
        "description": "Follow line continuously until lost"
    },
    "line_stop": {
        "handler": LineHandler.line_stop,
        "opcode": "LineStop",
        "arguments": 0,
        "category": "line",
        "description": "Stop line following (stop motors)"
    },
    "line_intersection_stop": {
        "handler": LineHandler.line_intersection_stop,
        "opcode": "LineIntersectionStop",
        "arguments": 2,
        "category": "line",
        "description": "Stop at line intersection"
    },
    "set_mp3_play": {
        "handler": PeripheralHandler.set_mp3_play,
        "opcode": "SetMp3Play",
        "arguments": 1,
        "category": "peripheral",
        "description": "Play MP3 track (adapted to active buzzer beep)"
    },
}
