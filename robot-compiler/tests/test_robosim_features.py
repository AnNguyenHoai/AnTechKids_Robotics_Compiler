import unittest
import tempfile
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from compiler.compiler import RobotCompiler


class TestRoboSimFeatures(unittest.TestCase):
    def test_import_thread(self):
        source = """
import _thread
def task():
    pass
_thread.start_new_thread(task, ())
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py') as f:
            f.write(source)
            f.flush()
            compiler = RobotCompiler()
            program = compiler.compile(f.name)
            self.assertIsNotNone(program)
            # Kiểm tra không có lỗi, có thể kiểm tra số instruction nếu muốn

    def test_while_true(self):
        source = """
while 1:
    pass
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py') as f:
            f.write(source)
            f.flush()
            compiler = RobotCompiler()
            program = compiler.compile(f.name)
            self.assertIsNotNone(program)
            # Ít nhất có một jump
            self.assertGreater(len(program.instructions), 0)

    def test_full_robosim(self):
        source = """
import rcu
import _thread

def task():
    rcu.SetMoveRunSecond("forward", 50, 1)

_thread.start_new_thread(task, ())
while 1:
    pass
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py') as f:
            f.write(source)
            f.flush()
            compiler = RobotCompiler()
            program = compiler.compile(f.name)
            self.assertIsNotNone(program)
            # Kiểm tra số instruction
            self.assertGreater(len(program.instructions), 5)