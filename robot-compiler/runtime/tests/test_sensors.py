# runtime/tests/test_sensors.py
import unittest
import sys
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.hardware.mock import MockHardware
from runtime.sensors import (
    SensorManager, LineSensor, UltrasonicSensor, TouchSensor,
    LightSensor, ColorSensor, create_mock_sensors,
    MovingAverageFilter, MedianFilter, ThresholdFilter
)

class TestSensorBase(unittest.TestCase):
    def setUp(self):
        self.hardware = MockHardware()

    def test_line_sensor(self):
        sensor = LineSensor(self.hardware, 0)
        self.hardware.set_line_value(0, 800)
        sensor.update()
        val = sensor.read()
        self.assertEqual(val.raw, 800)
        self.assertAlmostEqual(val.normalized, 800/1023, places=2)
        self.assertTrue(sensor.is_on_line(threshold=0.8))

    def test_ultrasonic(self):
        sensor = UltrasonicSensor(self.hardware)
        # Set distance less than threshold to trigger obstacle
        self.hardware.set_ultrasonic_value(20)  # 20 cm < 25 cm threshold
        sensor.update()
        val = sensor.read()
        self.assertEqual(val.raw, 20)
        self.assertAlmostEqual(val.normalized, 0.2, places=2)
        self.assertTrue(sensor.has_obstacle(threshold=25))

    def test_touch(self):
        sensor = TouchSensor(self.hardware, 0)
        self.hardware.set_touch_value(0, True)
        sensor.update()
        self.assertTrue(sensor.pressed())
        self.hardware.set_touch_value(0, False)
        sensor.update()
        self.assertFalse(sensor.pressed())

    def test_light_sensor(self):
        sensor = LightSensor(self.hardware, 0)
        self.hardware.set_line_value(0, 512)
        sensor.update()
        val = sensor.read()
        self.assertEqual(val.raw, 512)
        self.assertAlmostEqual(val.normalized, 0.5, places=2)

    def test_color_sensor(self):
        sensor = ColorSensor(self.hardware)
        sensor.update()  # mock values
        val = sensor.read()
        self.assertEqual(val.raw, (0,0,0))

    def test_sensor_manager(self):
        mgr = SensorManager()
        sensors = create_mock_sensors(self.hardware)
        for s in sensors.values():
            mgr.register(s)
        mgr.initialize_all()
        self.hardware.set_line_value(0, 900)
        mgr.update_all()
        val = mgr.read("line_0")
        self.assertIsNotNone(val)
        self.assertEqual(val.raw, 900)

    def test_filters(self):
        ma = MovingAverageFilter(3)
        self.assertEqual(ma.filter(10), 10)
        self.assertEqual(ma.filter(20), 15)
        self.assertEqual(ma.filter(30), 20)

        med = MedianFilter(3)
        med.filter(10)
        med.filter(30)
        self.assertEqual(med.filter(20), 20)

        th = ThresholdFilter(0.5, 0.1)
        self.assertFalse(th.filter(0.4))
        self.assertFalse(th.filter(0.45))
        self.assertTrue(th.filter(0.6))   # >= 0.6
        self.assertTrue(th.filter(0.55))  # hysteresis keeps true

if __name__ == "__main__":
    unittest.main()