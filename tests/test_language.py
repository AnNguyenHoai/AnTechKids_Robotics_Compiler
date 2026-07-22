import unittest
import subprocess
import sys
from pathlib import Path

class TestLanguage(unittest.TestCase):
    def test_build(self):
        script = Path(__file__).parent.parent / "robot-language" / "build.py"
        result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0,
                         msg=f"Language build failed:\n{result.stdout}\n{result.stderr}")