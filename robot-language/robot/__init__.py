"""
Robot Standard API Package (AUTO GENERATED)

This package is generated from specification/api.yaml.
DO NOT EDIT MANUALLY.
"""

from .motion import *
from .system import *
from .sensor import *
from .servo import *
from .led import *
from .motor import *
from .line import *
from .peripheral import *

__all__ = ['forward', 'backward', 'turn_left', 'turn_right', 'set_motor_speed', 'wait', 'stop', 'read_ultrasonic', 'read_touch', 'read_light', 'read_color', 'read_line', 'get_trace_value', 'get_trace_state', 'get_trace_raw', 'set_servo', 'set_3c_led', 'set_light_sensor_led', 'set_motor_straight_angle', 'line_basis', 'line_follow', 'line_stop', 'line_intersection_stop', 'set_mp3_play']

__version__ = "1.0.0"
