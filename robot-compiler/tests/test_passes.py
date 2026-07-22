import unittest
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from compiler.frontend.compiler import FrontendCompiler
from compiler.passes import PassContext, PassManager
from compiler.validation import ValidationPass
from compiler.canonicalization import CanonicalizationPass
from compiler.lowering import LoweringPass
from compiler.diagnostics import DiagnosticEngine


class TestPasses(unittest.TestCase):
    def test_validation_empty_program(self):
        from compiler.ir import IRProgram
        program = IRProgram()
        diag = DiagnosticEngine()
        context = PassContext(program, diag)
        pass_ = ValidationPass()
        result = pass_.run(context)
        self.assertFalse(result.success)
        self.assertTrue(diag.has_errors())

    def test_validation_duplicate_function(self):
        from compiler.ir import IRProgram, IRFunction
        program = IRProgram()
        program.add_function(IRFunction("main"))
        program.add_function(IRFunction("main"))
        diag = DiagnosticEngine()
        context = PassContext(program, diag)
        pass_ = ValidationPass()
        result = pass_.run(context)
        self.assertFalse(result.success)
        self.assertTrue(diag.has_errors())

    def test_canonicalization_direction(self):
        source = """
import rcu
rcu.SetMoveRun("FORWARD", 50)
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(source)
            path = Path(f.name)

        compiler = FrontendCompiler()
        program = compiler.compile(path)
        func = program.functions[0]
        ins = func.blocks[0].instructions[0]
        self.assertEqual(ins.operands[0].as_string(), "forward")