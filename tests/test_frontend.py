import unittest
import subprocess
import sys
from pathlib import Path

class TestFrontend(unittest.TestCase):
    def test_frontend_suite(self):
        script = Path(__file__).parent.parent / "robot-frontend-robosim" / "test" / "run_tests.py"
        result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0,
                         msg=f"Frontend test failed:\n{result.stdout}\n{result.stderr}")