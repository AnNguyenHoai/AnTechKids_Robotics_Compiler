import unittest
import sys
from pathlib import Path
import io

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from compiler.frontend.compiler import FrontendCompiler
from compiler.ir.printer import IRPrinter


class TestGolden(unittest.TestCase):
    def test_demo_forward(self):
        source_file = ROOT / "examples" / "demo_forward.py"
        golden_file = ROOT / "tests" / "golden" / "demo_forward.ir"
        compiler = FrontendCompiler()
        program = compiler.compile(source_file)

        output = io.StringIO()
        IRPrinter.print(program, output)
        printed = output.getvalue()

        # Read golden
        with open(golden_file, 'r', encoding='utf-8') as f:
            expected = f.read()

        def normalize(text):
            """Remove Source lines and strip all lines."""
            lines = []
            for line in text.splitlines():
                line = line.strip()
                if "Source:" in line:
                    continue  # skip source location lines
                if not line:
                    continue  # skip empty lines
                lines.append(line)
            return "\n".join(lines)

        printed_norm = normalize(printed)
        expected_norm = normalize(expected)

        self.assertEqual(printed_norm, expected_norm)