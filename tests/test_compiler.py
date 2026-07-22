import unittest
import subprocess
import sys
from pathlib import Path

class TestCompiler(unittest.TestCase):
    def test_compiler_suite(self):
        script = Path(__file__).parent.parent / "robot-compiler" / "test" / "run_tests.py"
        result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, 
                         msg=f"Compiler test failed:\n{result.stdout}\n{result.stderr}")