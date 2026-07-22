"""
Unit Tests for Standard Robot API

These tests verify that the Standard Robot API functions:
1. Are callable (no syntax errors)
2. Do not raise exceptions
3. Are correctly exported via __all__

Note: These tests do NOT verify hardware behavior.
The actual execution logic is implemented in:
- robot-compiler (bytecode generation)
- robot-platform (VM and RobotAPI)
- hardware (ESP32)
"""

import sys
from pathlib import Path

# Thêm đường dẫn robot-language vào sys.path để import được module robot
sys.path.insert(0, str(Path(__file__).parent.parent))

import unittest
from robot import *


class TestMotionAPI(unittest.TestCase):
    """Test motion control functions."""

    def test_forward(self):
        """forward(speed) should be callable."""
        try:
            forward(50)
        except Exception as e:
            self.fail(f"forward(50) raised an exception: {e}")

    def test_backward(self):
        """backward(speed) should be callable."""
        try:
            backward(50)
        except Exception as e:
            self.fail(f"backward(50) raised an exception: {e}")

    def test_left(self):
        """left(speed) should be callable."""
        try:
            left(50)
        except Exception as e:
            self.fail(f"left(50) raised an exception: {e}")

    def test_right(self):
        """right(speed) should be callable."""
        try:
            right(50)
        except Exception as e:
            self.fail(f"right(50) raised an exception: {e}")

    def test_stop(self):
        """stop() should be callable."""
        try:
            stop()
        except Exception as e:
            self.fail(f"stop() raised an exception: {e}")


class TestTimingAPI(unittest.TestCase):
    """Test timing control functions."""

    def test_wait(self):
        """wait(milliseconds) should be callable."""
        try:
            wait(1000)
        except Exception as e:
            self.fail(f"wait(1000) raised an exception: {e}")


class TestImport(unittest.TestCase):
    """Test import behavior."""

    def test_import_all(self):
        """All functions should be available via from robot import *."""
        expected_functions = [
            "forward",
            "backward",
            "left",
            "right",
            "stop",
            "wait",
        ]
        for name in expected_functions:
            self.assertIn(name, globals(),
                          f"Function '{name}' not imported via 'from robot import *'")

    def test_package_version(self):
        """Package should have a __version__ attribute."""
        import robot
        self.assertTrue(hasattr(robot, "__version__"))
        self.assertEqual(robot.__version__, "1.0.0")


if __name__ == "__main__":
    unittest.main()