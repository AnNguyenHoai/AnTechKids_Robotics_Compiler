# runtime/hardware/esp32/motor_driver.py
from ..interfaces import IMotorDriver
from .board_config import BoardConfiguration
from .logger import ESP32Logger

class ESP32MotorDriver(IMotorDriver):
    def __init__(self, config: BoardConfiguration, logger: ESP32Logger):
        self.config = config
        self.logger = logger
        self._last_left = 0
        self._last_right = 0
        self.logger.info(f"Motor driver initialized: left_pin={config.left_motor_pin}, right_pin={config.right_motor_pin}")

    def set_motor(self, left_pwm: int, right_pwm: int) -> None:
        # Clamp values
        left = max(-100, min(100, left_pwm))
        right = max(-100, min(100, right_pwm))
        self._last_left = left
        self._last_right = right
        self.logger.debug(f"Set motor: L={left}, R={right}")
        # In real implementation: analogWrite(pin, map(left, -100, 100, 0, 255)) etc.

    def stop(self) -> None:
        self.logger.debug("Motor stop")
        self.set_motor(0, 0)

    def brake(self) -> None:
        self.logger.debug("Motor brake")
        # In real implementation: set both pins HIGH (or LOW depending on H-bridge)
        # Here we just stop
        self.stop()