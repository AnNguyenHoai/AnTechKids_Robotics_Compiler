import unittest
from pathlib import Path
import tempfile
from compiler.frontend.compiler import FrontendCompiler
from compiler.ir.printer import IRPrinter
import io


class TestASTToIR(unittest.TestCase):
    def setUp(self):
        self.compiler = FrontendCompiler()

    def test_forward_program(self):
        source = """
import rcu
rcu.SetMoveRun("forward", 50)
rcu.SetMoveStop()
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(source)
            path = Path(f.name)

        program = self.compiler.compile(path)
        self.assertEqual(len(program.functions), 1)  # main
        main = program.functions[0]
        self.assertEqual(main.name, "main")
        self.assertEqual(len(main.blocks), 1)
        block = main.blocks[0]
        self.assertEqual(len(block.instructions), 2)
        ins0 = block.instructions[0]
        self.assertEqual(ins0.opcode.name, "MOVE_RUN")
        self.assertEqual(ins0.operands[0].as_string(), "forward")
        self.assertEqual(ins0.operands[1].as_integer(), 50)
        ins1 = block.instructions[1]
        self.assertEqual(ins1.opcode.name, "MOVE_STOP")

    def test_wait_program(self):
        source = """
import rcu
rcu.SetWaitForTime(1.0)
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(source)
            path = Path(f.name)

        program = self.compiler.compile(path)
        main = program.functions[0]
        ins = main.blocks[0].instructions[0]
        self.assertEqual(ins.opcode.name, "WAIT")
        self.assertEqual(ins.operands[0].as_integer(), 1000)

    def test_move_run_time(self):
        source = """
import rcu
rcu.SetMoveRunSecond("backward", 30, 2.5)
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(source)
            path = Path(f.name)

        program = self.compiler.compile(path)
        main = program.functions[0]
        ins = main.blocks[0].instructions[0]
        self.assertEqual(ins.opcode.name, "MOVE_RUN_TIME")
        self.assertEqual(ins.operands[0].as_string(), "backward")
        self.assertEqual(ins.operands[1].as_integer(), 30)
        self.assertEqual(ins.operands[2].as_integer(), 2500)

    def test_unknown_api(self):
        source = """
import rcu
rcu.UnknownAPI()
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(source)
            path = Path(f.name)

        with self.assertRaises(Exception) as ctx:
            self.compiler.compile(path)
        self.assertIn("Unknown RoboSim API", str(ctx.exception))

    def test_printer_output(self):
        source = """
import rcu
rcu.SetMoveRun("forward", 50)
rcu.SetWaitForTime(1.0)
rcu.SetMoveStop()
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(source)
            path = Path(f.name)

        program = self.compiler.compile(path)
        output = io.StringIO()
        IRPrinter.print(program, output)
        printed = output.getvalue()
        self.assertIn("MOVE_RUN", printed)
        self.assertIn("WAIT", printed)
        self.assertIn("MOVE_STOP", printed)

    def test_source_location(self):
        source = """
import rcu
rcu.SetMoveRun("forward", 50)
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(source)
            path = Path(f.name)

        program = self.compiler.compile(path)
        main = program.functions[0]
        ins = main.blocks[0].instructions[0]
        self.assertIsNotNone(ins.location)
        self.assertEqual(ins.location.line, 3)
        self.assertIn("forward", ins.operands[0].as_string())


if __name__ == "__main__":
    unittest.main()