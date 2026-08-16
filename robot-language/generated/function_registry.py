"""
AUTO GENERATED FILE
"""

from compiler.handlers.motion_handler import MotionHandler
from compiler.handlers.system_handler import SystemHandler
from compiler.handlers.sensor_handler import SensorHandler
from compiler.handlers.led_handler import LedHandler
from compiler.handlers.servo_handler import ServoHandler
from compiler.handlers.motor_handler import MotorHandler
from compiler.handlers.line_handler import LineHandler
from compiler.handlers.peripheral_handler import PeripheralHandler
from compiler.handlers.gui_handler import GuiHandler

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
    "set_move_initialize": {
        "handler": MotionHandler.set_move_initialize,
        "opcode": "MoveInitialize",
        "arguments": 3,
        "category": "motion",
        "description": "Configure drive motors (left/right ports and reverse mode)"
    },
    "set_move_run_angle": {
        "handler": MotionHandler.set_move_run_angle,
        "opcode": "MoveRunAngle",
        "arguments": 3,
        "category": "motion",
        "description": "Move for a specified angle (wheel rotation or chassis turn)"
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
    "get_light_sensor_data": {
        "handler": SensorHandler.get_light_sensor_data,
        "opcode": "GetLightSensorData",
        "arguments": 1,
        "category": "sensor",
        "description": "Read light sensor digital state (0/1)"
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
    "set_servo": {
        "handler": ServoHandler.set_servo,
        "opcode": "SetServo",
        "arguments": 2,
        "category": "servo",
        "description": "Set servo angle"
    },
    "set_seering_engine": {
        "handler": ServoHandler.set_seering_engine,
        "opcode": "SetSeeringEngine",
        "arguments": 2,
        "category": "servo",
        "description": "Set steering engine angle"
    },
    "set_seering_engine_time": {
        "handler": ServoHandler.set_seering_engine_time,
        "opcode": "SetSeeringEngineTime",
        "arguments": 3,
        "category": "servo",
        "description": "Set steering engine angle and hold for time"
    },
    "set_motor": {
        "handler": MotorHandler.set_motor,
        "opcode": "SetMotor",
        "arguments": 2,
        "category": "motor",
        "description": "Set speed of a DC motor on given port"
    },
    "set_motor_servo": {
        "handler": MotorHandler.set_motor_servo,
        "opcode": "SetMotorServo",
        "arguments": 3,
        "category": "motor",
        "description": "Set motor+servo combination"
    },
    "set_motor_straight_angle": {
        "handler": MotorHandler.set_motor_straight_angle,
        "opcode": "SetMotorStraightAngle",
        "arguments": 4,
        "category": "motor",
        "description": "Move both motors for a given angle"
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
    "line_millisecond": {
        "handler": LineHandler.line_millisecond,
        "opcode": "LineMillisecond",
        "arguments": 2,
        "category": "line",
        "description": "Line follow for a specified time (ms), blocking"
    },
    "line_intersection_stop": {
        "handler": LineHandler.line_intersection_stop,
        "opcode": "LineIntersectionStop",
        "arguments": 2,
        "category": "line",
        "description": "Follow line until intersection, then stop"
    },
    "line_turn_encounterline": {
        "handler": LineHandler.line_turn_encounterline,
        "opcode": "LineTurnEncounterLine",
        "arguments": 3,
        "category": "line",
        "description": "Turn until a line is encountered"
    },
    "line_for_bmp": {
        "handler": LineHandler.line_for_bmp,
        "opcode": "LineForBmp",
        "arguments": 2,
        "category": "line",
        "description": "Follow line for a given degree (time-based)"
    },
    "line_set_initialize": {
        "handler": LineHandler.line_set_initialize,
        "opcode": "LineSetInitialize",
        "arguments": 3,
        "category": "line",
        "description": "Initialize line sensor parameters"
    },
    "set_mp3_play": {
        "handler": PeripheralHandler.set_mp3_play,
        "opcode": "SetMp3Play",
        "arguments": 1,
        "category": "peripheral",
        "description": "Play MP3 track (adapted to active buzzer beep)"
    },
    "set_lizard": {
        "handler": PeripheralHandler.set_lizard,
        "opcode": "SetLizard",
        "arguments": 1,
        "category": "peripheral",
        "description": "Control peripheral lizard (unknown)"
    },
    "update_var": {
        "handler": GuiHandler.update_var,
        "opcode": "UpdateVar",
        "arguments": 2,
        "category": "gui",
        "description": "Update variable display in GUI"
    },
    "display_variable": {
        "handler": GuiHandler.display_variable,
        "opcode": "DisplayVariable",
        "arguments": 1,
        "category": "gui",
        "description": "Display variable value in GUI"
    },
}
