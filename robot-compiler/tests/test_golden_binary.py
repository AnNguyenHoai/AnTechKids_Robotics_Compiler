import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from compiler.frontend.compiler import FrontendCompiler
from compiler.passes import PassContext, PassManager
from compiler.isa import BackendLowering
from compiler.binary import ProgramEncoder, BinarySerializer, BinaryHeader, BinaryReader
from compiler.diagnostics import DiagnosticEngine

HEADER_SIZE = 19  # phải khớp với BinaryHeader.size()

class TestGoldenBinary(unittest.TestCase):
    def _compile_and_encode(self, source_file):
        compiler = FrontendCompiler()
        ir_prog = compiler.compile(source_file)
        diag = DiagnosticEngine()
        context = PassContext(ir_prog, diag)
        manager = PassManager()
        manager.register(BackendLowering())
        manager.run(context)
        isa_prog = context.config["isa_program"]
        encoder = ProgramEncoder()
        binary_prog = encoder.encode(isa_prog)
        serializer = BinarySerializer()
        return serializer.serialize(binary_prog)

    def test_demo_forward(self):
        source_file = ROOT / "examples" / "demo_forward.py"
        binary = self._compile_and_encode(source_file)
        # Đọc header từ 19 bytes đầu
        header = BinaryHeader.from_bytes(binary[:HEADER_SIZE])
        self.assertEqual(header.magic, 0x4E494252)
        self.assertGreater(len(binary), 16)

    def test_demo_wait(self):
        source_file = ROOT / "examples" / "demo_wait.py"
        golden_file = ROOT / "tests" / "golden" / "binary" / "demo_wait.bin"
        if not golden_file.exists():
            self.skipTest(f"Golden file not found: {golden_file}")
        binary = self._compile_and_encode(source_file)
        with open(golden_file, 'rb') as f:
            expected = f.read()
        self.assertEqual(binary, expected)

    def test_demo_move_stop(self):
        source_file = ROOT / "examples" / "demo_move_stop.py"
        golden_file = ROOT / "tests" / "golden" / "binary" / "demo_move_stop.bin"
        if not golden_file.exists():
            self.skipTest(f"Golden file not found: {golden_file}")
        binary = self._compile_and_encode(source_file)
        with open(golden_file, 'rb') as f:
            expected = f.read()
        self.assertEqual(binary, expected)