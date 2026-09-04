import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMPILER_ROOT = ROOT / "robot-compiler"
FRONTEND_ROOT = ROOT / "robot-frontend-robosim"
E2E_ROOT = COMPILER_ROOT / "integration" / "end_to_end"

for path in (COMPILER_ROOT, FRONTEND_ROOT, E2E_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from compiler.binary import ProgramEncoder
from compiler.isa import ISAFunction, ISAProgram
from runtime import MockHardware, ProgramLoader, VirtualMachine
from test_end_to_end import compile_robosim, convert_instruction

from oracle import assert_trace, event, normalize_hardware_log


class UnifiedE2EOracleTests(unittest.TestCase):
    def _execute(self, source: str):
        import tempfile

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as handle:
            handle.write(source)
            source_path = Path(handle.name)

        try:
            program = compile_robosim(source_path)
            isa_program = ISAProgram()
            main = ISAFunction("main")
            for instruction in program.instructions:
                main.add_instruction(convert_instruction(instruction))
            isa_program.add_function(main)

            binary_program = ProgramEncoder().encode(isa_program)
            runtime_program = ProgramLoader().load(binary_program)
            hardware = MockHardware()
            vm = VirtualMachine(hardware=hardware)
            vm.load(runtime_program)
            vm.run()

            self.assertEqual(vm.state.value, "finished")
            return normalize_hardware_log(hardware.log)
        finally:
            source_path.unlink(missing_ok=True)

    def test_motion_semantics_are_runtime_neutral(self):
        actual = self._execute("forward(80)\nstop()\n")
        expected = (
            event("motor", 80, 80),
            event("motor", 0, 0),
        )
        assert_trace(actual, expected)

    def test_wait_semantics_are_runtime_neutral(self):
        actual = self._execute("wait(100)\n")
        expected = (event("delay_ms", 100),)
        assert_trace(actual, expected)

    def test_turn_semantics_are_runtime_neutral(self):
        source = """turn_left(60)
stop()
turn_right(60)
stop()
"""
        actual = self._execute(source)
        expected = (
            event("motor", -60, 60),
            event("motor", 0, 0),
            event("motor", 60, -60),
            event("motor", 0, 0),
        )
        assert_trace(actual, expected)

    def test_oracle_does_not_depend_on_opcode_numbers(self):
        from oracle import TraceEvent

        actual = (TraceEvent("motor", (80, 80)),)
        expected = (event("motor", 80, 80),)
        assert_trace(actual, expected)

    def test_mismatch_reports_first_semantic_difference(self):
        from oracle import compare_trace

        actual = (event("motor", 80, 80), event("motor", 10, 10))
        expected = (event("motor", 80, 80), event("motor", 0, 0))
        ok, detail = compare_trace(actual, expected)
        self.assertFalse(ok)
        self.assertIn("first mismatch at index 1", detail)


if __name__ == "__main__":
    unittest.main()
