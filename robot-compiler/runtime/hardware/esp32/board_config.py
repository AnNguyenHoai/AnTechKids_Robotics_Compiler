# runtime/hardware/esp32/board_config.py
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class BoardConfiguration:
    # Motor pins
    left_motor_pin: int
    right_motor_pin: int
    pwm_channel_left: int
    pwm_channel_right: int
    pwm_frequency: int = 5000
    pwm_resolution: int = 8  # bits

    # Sensor pins (out of scope for this sprint, but placeholder)
    ultrasonic_trig_pin: int = 0
    ultrasonic_echo_pin: int = 0
    line_sensor_pins: Optional[List[int]] = None
    touch_sensor_pins: Optional[List[int]] = None

    # UART, SPI, I2C configs (future)
    uart_baudrate: int = 115200
    i2c_frequency: int = 400000
    spi_frequency: int = 1000000