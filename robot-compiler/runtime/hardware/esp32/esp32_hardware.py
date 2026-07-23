# runtime/hardware/esp32/esp32_hardware.py
from ..interface import IHardware
from .board_config import BoardConfiguration
from .hardware_capabilities import HardwareCapabilities
from .motor_driver import ESP32MotorDriver
from .timer import ESP32Timer
from .logger import ESP32Logger

class ESP32Hardware(IHardware):
    def __init__(self, config: BoardConfiguration, logger: ESP32Logger = None):
        self.config = config
        self.logger = logger or ESP32Logger("INFO")
        self.capabilities = HardwareCapabilities()
        self.timer = ESP32Timer()
        self.motor = ESP32MotorDriver(config, self.logger)

        # Mock sensor values (can be set for testing)
        self._ultrasonic_value = 50
        self._line_values = {0: 512, 1: 512, 2: 512}
        self._touch_values = {0: False, 1: False}

    # ---- IHardware implementation ----
    def set_motor(self, left: int, right: int) -> None:
        self.motor.set_motor(left, right)

    def delay(self, ms: int) -> None:
        self.timer.delay(ms)

    def read_ultrasonic(self) -> int:
        self.logger.debug("Read ultrasonic")
        return self._ultrasonic_value

    def read_line_sensor(self, channel: int) -> int:
        self.logger.debug(f"Read line sensor channel {channel}")
        return self._line_values.get(channel, 512)

    def read_touch(self, port: int) -> bool:
        self.logger.debug(f"Read touch port {port}")
        return self._touch_values.get(port, False)

    # ---- Test helpers ----
    def set_ultrasonic_value(self, value: int) -> None:
        self._ultrasonic_value = value

    def set_line_value(self, channel: int, value: int) -> None:
        self._line_values[channel] = value

    def set_touch_value(self, port: int, value: bool) -> None:
        self._touch_values[port] = value