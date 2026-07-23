# runtime/robot/runtime.py
from .interface import IRobot
from .motion import MotionController
from .sensor import SensorManager
from ..hardware.interface import IHardware

class RobotRuntime(IRobot):
    """Main robot runtime that orchestrates motion and sensors."""

    def __init__(self, hardware: IHardware):
        self.hardware = hardware
        self.motion = MotionController(hardware)
        self.sensors = SensorManager(hardware)

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

    def read_ultrasonic(self) -> int:
        return self.sensors.read_ultrasonic()

    def read_line_sensor(self, channel: int) -> int:
        return self.sensors.read_line_sensor(channel)

    # ---- State & Events ----

    def get_state(self):
        return self.motion.get_state()

    def get_events(self):
        return self.motion.get_events()

    def clear_events(self):
        self.motion.clear_events()