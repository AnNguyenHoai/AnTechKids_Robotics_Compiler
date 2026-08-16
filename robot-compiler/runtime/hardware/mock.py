# runtime/hardware/mock.py
import time
from .interface import IHardware

class MockHardware(IHardware):
    """Mock hardware implementation for testing and simulation."""

    def __init__(self):
        self.motor_left = 0
        self.motor_right = 0
        self.log = []
        self._ultrasonic_value = 50
        self._line_values = {0: 512, 1: 512, 2: 512}
        self._touch_values = {0: False, 1: False}
        self._light_value = 512
        self._color_value = 0

    def set_motor(self, left: int, right: int) -> None:
        self.motor_left = max(-100, min(100, left))
        self.motor_right = max(-100, min(100, right))
        self.log.append(("set_motor", self.motor_left, self.motor_right))
        print(f"[MockHardware] Motors: L={self.motor_left}, R={self.motor_right}")

    def delay(self, ms: int) -> None:
        self.log.append(("delay", ms))
        print(f"[MockHardware] Delay {ms} ms")
        time.sleep(ms / 1000.0)

    def read_ultrasonic(self) -> int:
        self.log.append(("read_ultrasonic",))
        print(f"[MockHardware] Read Ultrasonic: {self._ultrasonic_value} cm")
        return self._ultrasonic_value

    def read_line_sensor(self, channel: int) -> int:
        self.log.append(("read_line_sensor", channel))
        val = self._line_values.get(channel, 512)
        print(f"[MockHardware] Read Line Sensor channel {channel}: {val}")
        return val

    def read_touch(self, port: int) -> bool:
        self.log.append(("read_touch", port))
        val = self._touch_values.get(port, False)
        print(f"[MockHardware] Read Touch port {port}: {val}")
        return val

    def read_light(self, channel: int) -> int:
        self.log.append(("read_light", channel))
        print(f"[MockHardware] Read Light channel {channel}: {self._light_value}")
        return self._light_value

    def read_color(self) -> int:
        self.log.append(("read_color",))
        print(f"[MockHardware] Read Color: {self._color_value}")
        return self._color_value

    # ---- Test helpers ----
    def set_ultrasonic_value(self, value: int):
        self._ultrasonic_value = value

    def set_line_value(self, channel: int, value: int):
        self._line_values[channel] = value

    def set_touch_value(self, port: int, value: bool):
        self._touch_values[port] = value

    def set_light_value(self, value: int):
        self._light_value = value

    def set_color_value(self, value: int):
        self._color_value = value

    def get_log(self):
        return self.log

    def clear_log(self):
        self.log.clear()