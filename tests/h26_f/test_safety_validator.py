import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "robot-compiler"))
from compiler.safety_validator import validate_instructions


def ins(opcode, p1=0, p2=0, p3=0, p4=0):
    return SimpleNamespace(opcode=SimpleNamespace(value=opcode), p1=p1, p2=p2, p3=p3, p4=p4)


class H26FSafetyTests(unittest.TestCase):
    def test_accepts_program_within_limits(self):
        self.assertEqual(validate_instructions([ins(2, 0)]), ())

    def test_rejects_unknown_opcode(self):
        violations = validate_instructions([ins(250)])
        self.assertTrue(any(v.rule == "invalid_opcode" for v in violations))

    def test_rejects_variable_index_overflow(self):
        violations = validate_instructions([ins(2, 32)])
        self.assertTrue(any(v.rule == "invalid_variable" for v in violations))

    def test_rejects_invalid_jump_target(self):
        violations = validate_instructions([ins(14, 0, 2)])
        self.assertTrue(any(v.rule == "invalid_jump" for v in violations))

    def test_allows_jump_to_end(self):
        self.assertEqual(validate_instructions([ins(14, 0, 1)]), ())

    def test_rejects_linear_call_stack_overflow(self):
        violations = validate_instructions([ins(27)] * 9)
        self.assertTrue(any(v.rule == "stack_overflow" for v in violations))

    def test_rejects_unsupported_capability(self):
        violations = validate_instructions([ins(30, 0)], target_capabilities=["motion.basic"])
        self.assertTrue(any(v.rule == "unsupported_capability" for v in violations))

    def test_robostudio_bridge_enforces_safety_gate(self):
        bridge = (ROOT / "robot-compiler" / "compiler" / "robostudio_bridge.py").read_text(encoding="utf-8")
        self.assertIn("from compiler.safety_validator import validate_program", bridge)
        self.assertIn("violations = validate_program(program)", bridge)
        self.assertIn("code=first.rule.upper()", bridge)

    def test_firmware_program_load_failure_keeps_recovery_services_reachable(self):
        main = (ROOT / "robot-platform" / "main" / "main.ino").read_text(encoding="utf-8")
        self.assertIn("g_programLoadFailed = true", main)
        self.assertIn("SAFE RECOVERY", main)
        self.assertNotIn('BootLogger::log("ERROR", "Failed to load program. Halted.");', main)

    def test_resource_limit_is_contract_driven(self):
        resources = {
            "program": {"max_instructions": 1},
            "runtime": {"max_variables": 32, "max_call_stack": 8, "max_loop_depth": 8},
            "operands": {"min": -2147483648, "max": 2147483647},
            "jump_targets": {"allow_end": True},
        }
        violations = validate_instructions([ins(2), ins(2)], resource_contract=resources)
        self.assertTrue(any(v.rule == "program_overflow" for v in violations))


if __name__ == "__main__":
    unittest.main()
