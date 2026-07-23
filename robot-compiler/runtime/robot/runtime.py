# runtime/robot/runtime.py
from .interface import IRobot
from .motion import MotionController
from ..sensors.sensor_manager import SensorManager
from ..sensors.line_sensor import LineSensor
from ..sensors.ultrasonic_sensor import UltrasonicSensor
from ..sensors.touch_sensor import TouchSensor
from ..sensors.light_sensor import LightSensor
from ..sensors.color_sensor import ColorSensor
from ..hardware.interface import IHardware
from typing import Dict, Any

class RobotRuntime(IRobot):
    """Main robot runtime that orchestrates motion and sensors."""

    def __init__(self, hardware: IHardware):
        self.hardware = hardware
        self.motion = MotionController(hardware)
        # Initialize sensor manager and register sensors
        self.sensor_manager = SensorManager()
        self._register_sensors()

    def _register_sensors(self):
        # Register line sensors (3 channels)
        for ch in range(3):
            sensor = LineSensor(self.hardware, ch, f"line_{ch}")
            self.sensor_manager.register(sensor)
        # Register ultrasonic
        self.sensor_manager.register(UltrasonicSensor(self.hardware, "ultrasonic"))
        # Register touch sensors (2 ports)
        for port in range(2):
            sensor = TouchSensor(self.hardware, port, f"touch_{port}")
            self.sensor_manager.register(sensor)
        # Register light sensor (use channel 0 for demo)
        self.sensor_manager.register(LightSensor(self.hardware, 0, "light"))
        # Register color sensor (placeholder)
        self.sensor_manager.register(ColorSensor(self.hardware, "color"))

    # ---- Motion APIs ----
    def forward(self, speed: int) -> None:
        self.motion.forward(speed)

    def backward(self, speed: int) -> None:
        self.motion.backward(speed)

    def left(self, speed: int) -> None:
        self.motion.left(speed)

    def right(self, speed: int) -> None:
        self.motion.right(speed)

    def stop(self) -> None:
        self.motion.stop()

    def wait(self, ms: int) -> None:
        self.motion.wait(ms)

    def set_motor(self, left: int, right: int) -> None:
        self.hardware.set_motor(left, right)

    # ---- Sensor APIs ----
    def read_line_sensor(self, channel: int) -> int:
        # For backward compatibility, read raw value
        val = self.sensor_manager.read(f"line_{channel}")
        if val:
            return val.raw
        return 0

    def read_ultrasonic(self) -> int:
        val = self.sensor_manager.read("ultrasonic")
        if val:
            return val.raw
        return 0

    def read_touch(self, port: int) -> bool:
        val = self.sensor_manager.read(f"touch_{port}")
        if val:
            return val.raw
        return False

    # ---- State & Events ----
    def get_state(self):
        return self.motion.get_state()

    def get_events(self):
        return self.motion.get_events()

    def clear_events(self):
        self.motion.clear_events()

    def update_sensors(self):
        """Update all sensors (should be called periodically)."""
        self.sensor_manager.update_all()