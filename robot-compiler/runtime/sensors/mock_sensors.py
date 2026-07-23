# runtime/sensors/mock_sensors.py
from .base import ISensor
from .sensor_value import SensorValue
from .line_sensor import LineSensor
from .ultrasonic_sensor import UltrasonicSensor
from .touch_sensor import TouchSensor
from .light_sensor import LightSensor
from .color_sensor import ColorSensor
from ..hardware.mock import MockHardware

def create_mock_sensors(hardware: MockHardware):
    """Factory to create a set of mock sensors."""
    sensors = {
        "line_0": LineSensor(hardware, 0, "line"),
        "line_1": LineSensor(hardware, 1, "line"),
        "line_2": LineSensor(hardware, 2, "line"),
        "ultrasonic": UltrasonicSensor(hardware, "ultrasonic"),
        "touch_0": TouchSensor(hardware, 0, "touch"),
        "touch_1": TouchSensor(hardware, 1, "touch"),
        "light_0": LightSensor(hardware, 0, "light"),
        "color": ColorSensor(hardware, "color"),
    }
    return sensors