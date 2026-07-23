# runtime/robot/sensor.py
from ..hardware.interface import IHardware

class SensorManager:
    def __init__(self, hardware: IHardware):
        self.hardware = hardware
        self._sensor_values = {}

    def read_ultrasonic(self) -> int:
        return self.hardware.read_ultrasonic()

    def read_line_sensor(self, channel: int) -> int:
        return self.hardware.read_line_sensor(channel)

    def read_touch(self, port: int) -> bool:
        return self.hardware.read_touch(port)

    # Future sensors can be added here