# runtime/tests/test_esp32_adapter.py
import unittest
import sys
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.hardware import BoardConfiguration, ESP32Hardware, ESP32Logger, HardwareCapabilities


class TestESP32Adapter(unittest.TestCase):
    def setUp(self):
        self.config = BoardConfiguration(
            left_motor_pin=25,
            right_motor_pin=26,
            pwm_channel_left=0,
            pwm_channel_right=1,
        )
        self.logger = ESP32Logger("DEBUG")

    def test_board_config(self):
        self.assertEqual(self.config.left_motor_pin, 25)
        self.assertEqual(self.config.right_motor_pin, 26)
        self.assertEqual(self.config.pwm_channel_left, 0)
        self.assertEqual(self.config.pwm_channel_right, 1)

    def test_hardware_initialization(self):
        hw = ESP32Hardware(self.config, self.logger)
        self.assertIsNotNone(hw.motor)
        self.assertIsNotNone(hw.timer)
        self.assertIsNotNone(hw.capabilities)
        self.assertIsInstance(hw.capabilities, HardwareCapabilities)
        self.assertTrue(hw.capabilities.supports_pwm)

    def test_set_motor(self):
        hw = ESP32Hardware(self.config, self.logger)
        hw.set_motor(80, -60)
        # Just ensure no exception
        self.assertEqual(hw.motor._last_left, 80)
        self.assertEqual(hw.motor._last_right, -60)

    def test_delay(self):
        hw = ESP32Hardware(self.config, self.logger)
        start = time.time()
        hw.delay(100)
        elapsed = time.time() - start
        self.assertAlmostEqual(elapsed, 0.1, places=1)

    def test_sensor_read(self):
        hw = ESP32Hardware(self.config, self.logger)
        hw.set_ultrasonic_value(30)
        self.assertEqual(hw.read_ultrasonic(), 30)
        hw.set_line_value(0, 700)
        self.assertEqual(hw.read_line_sensor(0), 700)
        hw.set_touch_value(1, True)
        self.assertTrue(hw.read_touch(1))

    def test_logger_levels(self):
        logger = ESP32Logger("INFO")
        # Should not raise
        logger.info("Info message")
        logger.warn("Warn message")
        logger.error("Error message")
        logger.debug("Debug message")  # Should not print (level INFO)

        logger_debug = ESP32Logger("DEBUG")
        logger_debug.debug("Debug message")  # Should print


if __name__ == "__main__":
    unittest.main()