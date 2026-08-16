# runtime/robot/runtime.py
from .interface import IRobot
from .motion import MotionController
from ..hardware.interface import IHardware

class RobotRuntime(IRobot):
    """Main robot runtime that orchestrates motion and sensors."""

    def __init__(self, hardware: IHardware):
        self.hardware = hardware
        self.motion = MotionController(hardware)

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

    # ---- Additional motor API for handlers ----
    def set_motor_speed(self, left: int, right: int) -> None:
        """Set left and right motor speeds directly."""
        self.hardware.set_motor(left, right)

    # ---- Output APIs ----
    def set_led(self, port: int, state: int) -> None:
        """Set LED state (mock logging)."""
        print(f"[RobotRuntime] set_led(port={port}, state={state})")
        # Optionally call hardware if it supports LED
        # self.hardware.set_led(port, state)

    def set_mp3_play(self, index: int) -> None:
        """Play beep (mock logging)."""
        print(f"[RobotRuntime] set_mp3_play(index={index})")

    # ---- Sensor APIs (call hardware directly for logging) ----
    def read_ultrasonic(self) -> int:
        return self.hardware.read_ultrasonic()

    def read_touch(self, port: int) -> int:
        return 1 if self.hardware.read_touch(port) else 0

    def read_light(self, channel: int) -> int:
        return self.hardware.read_light(channel)

    def read_line(self, channel: int) -> int:
        return self.hardware.read_line_sensor(channel)

    def read_color(self) -> int:
        return self.hardware.read_color()

    # ---- Legacy sensor method (for backward compatibility) ----
    def read_line_sensor(self, channel: int) -> int:
        return self.read_line(channel)

    # ---- State & Events ----
    def get_state(self):
        return self.motion.get_state()

    def get_events(self):
        return self.motion.get_events()

    def clear_events(self):
        self.motion.clear_events()