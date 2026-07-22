import unittest
import sys
from pathlib import Path
import io

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from compiler.frontend.compiler import FrontendCompiler
from compiler.passes import PassContext, PassManager
from compiler.diagnostics import DiagnosticEngine
from compiler.isa import BackendLowering, InstructionPrinter


class TestGoldenBackend(unittest.TestCase):
    def _normalize(self, text):
        lines = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            lines.append(line)
        return "\n".join(lines)

    def _compile_and_lower(self, source_file):
        compiler = FrontendCompiler()
        ir_prog = compiler.compile(source_file)
        diag = DiagnosticEngine()
        context = PassContext(ir_prog, diag)
        manager = PassManager()
        manager.register(BackendLowering())
        manager.run(context)
        return context.config["isa_program"]

    def test_demo_forward(self):
        source_file = ROOT / "examples" / "demo_forward.py"
        golden_file = ROOT / "tests" / "golden" / "backend" / "demo_forward.isa"

        isa_prog = self._compile_and_lower(source_file)
        output = io.StringIO()
        InstructionPrinter.print(isa_prog, output)
        printed = self._normalize(output.getvalue())

        with open(golden_file, 'r', encoding='utf-8') as f:
            expected = self._normalize(f.read())

        self.assertEqual(printed, expected)

    def test_demo_wait(self):
        source_file = ROOT / "examples" / "demo_wait.py"
        golden_file = ROOT / "tests" / "golden" / "backend" / "demo_wait.isa"

        isa_prog = self._compile_and_lower(source_file)
        output = io.StringIO()
        InstructionPrinter.print(isa_prog, output)
        printed = self._normalize(output.getvalue())

        with open(golden_file, 'r', encoding='utf-8') as f:
            expected = self._normalize(f.read())

        self.assertEqual(printed, expected)

    def test_demo_move_stop(self):
        source_file = ROOT / "examples" / "demo_move_stop.py"
        golden_file = ROOT / "tests" / "golden" / "backend" / "demo_move_stop.isa"

        isa_prog = self._compile_and_lower(source_file)
        output = io.StringIO()
        InstructionPrinter.print(isa_prog, output)
        printed = self._normalize(output.getvalue())

        with open(golden_file, 'r', encoding='utf-8') as f:
            expected = self._normalize(f.read())

        self.assertEqual(printed, expected)