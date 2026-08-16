"""
Robot Standard API Package (AUTO GENERATED)

This package is generated from specification/api.yaml.
DO NOT EDIT MANUALLY.
"""

from .motion import *
from .system import *
from .sensor import *
from .led import *
from .servo import *
from .motor import *
from .line import *
from .peripheral import *
from .gui import *

__all__ = ['forward', 'backward', 'turn_left', 'turn_right', 'set_motor_speed', 'set_move_initialize', 'set_move_run_angle', 'wait', 'stop', 'read_ultrasonic', 'read_touch', 'read_light', 'read_color', 'read_line', 'get_trace_value', 'get_trace_state', 'get_trace_raw', 'get_light_sensor_data', 'set_3c_led', 'set_light_sensor_led', 'set_servo', 'set_seering_engine', 'set_seering_engine_time', 'set_motor', 'set_motor_servo', 'set_motor_straight_angle', 'line_basis', 'line_follow', 'line_stop', 'line_millisecond', 'line_intersection_stop', 'line_turn_encounterline', 'line_for_bmp', 'line_set_initialize', 'set_mp3_play', 'set_lizard', 'update_var', 'display_variable']

__version__ = "1.0.0"
