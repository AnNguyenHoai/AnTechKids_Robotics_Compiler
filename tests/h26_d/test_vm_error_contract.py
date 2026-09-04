import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "packages" / "robot-isa" / "error_contract.json"
PY_ADAPTER = ROOT / "robot-compiler" / "compiler" / "error_contract.py"
CPP_ADAPTER = ROOT / "robot-platform" / "main" / "src" / "Services" / "VM" / "VMErrorContract.h"
VM_CPP = ROOT / "robot-platform" / "main" / "src" / "Services" / "VM" / "VM.cpp"
PROGRAM_H = ROOT / "robot-platform" / "main" / "src" / "Services" / "VM" / "Program.h"


class VMErrorContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads(MANIFEST.read_text(encoding="utf-8"))
        cls.entries = {entry["id"]: entry for entry in cls.contract["errors"]}

    def test_manifest_has_unique_codes_and_ids(self):
        entries = self.contract["errors"]
        self.assertEqual(len(entries), len({entry["code"] for entry in entries}))
        self.assertEqual(len(entries), len({entry["id"] for entry in entries}))
        self.assertIn("unknown_code", self.contract)

    def test_preserved_legacy_numeric_meanings(self):
        expected = {
            1: "invalid_opcode",
            3: "invalid_jump",
            4: "stack_overflow",
            5: "invalid_return",
            6: "division_by_zero",
            7: "modulo_by_zero",
        }
        actual = {entry["code"]: entry["id"] for entry in self.contract["errors"]}
        for code, error_id in expected.items():
            self.assertEqual(actual[code], error_id)

    def test_python_adapter_assignments_match_manifest(self):
        text = PY_ADAPTER.read_text(encoding="utf-8")
        assignments = dict(re.findall(r"^\s*([A-Z_]+)\s*=\s*(\d+)\s*$", text, re.MULTILINE))
        expected = {
            "OK": "0",
            "INVALID_OPCODE": "1",
            "PROGRAM_OVERFLOW": "2",
            "INVALID_JUMP": "3",
            "STACK_OVERFLOW": "4",
            "INVALID_RETURN": "5",
            "DIVISION_BY_ZERO": "6",
            "MODULO_BY_ZERO": "7",
            "INVALID_OPERAND": "8",
            "INVALID_VARIABLE": "9",
        }
        for name, value in expected.items():
            self.assertEqual(assignments.get(name), value)

    def test_cpp_adapter_enumeration_matches_manifest(self):
        text = CPP_ADAPTER.read_text(encoding="utf-8")
        expected = {
            "None": 0,
            "InvalidOpcode": 1,
            "ProgramOverflow": 2,
            "InvalidJump": 3,
            "StackOverflow": 4,
            "InvalidReturn": 5,
            "DivisionByZero": 6,
            "ModuloByZero": 7,
            "InvalidOperand": 8,
            "InvalidVariable": 9,
        }
        for name, code in expected.items():
            self.assertRegex(text, rf"\b{name}\s*=\s*{code}\b")
        self.assertIn("Unknown         = 0xFF", text)

    def test_vm_no_longer_contains_error_magic_numbers(self):
        text = VM_CPP.read_text(encoding="utf-8")
        forbidden = [
            "mContext.mErrorCode = 1",
            "mContext.mErrorCode = 3",
            "mContext.mErrorCode = 4",
            "mContext.mErrorCode = 5",
            "mContext.mErrorCode = 6",
            "mContext.mErrorCode = 7",
        ]
        for fragment in forbidden:
            self.assertNotIn(fragment, text)
        for symbol in (
            "VMErrorCode::InvalidOpcode",
            "VMErrorCode::InvalidJump",
            "VMErrorCode::StackOverflow",
            "VMErrorCode::InvalidReturn",
            "VMErrorCode::DivisionByZero",
            "VMErrorCode::ModuloByZero",
        ):
            self.assertIn(symbol, text)

    def test_program_overflow_is_reported_by_program_container(self):
        text = PROGRAM_H.read_text(encoding="utf-8")
        self.assertIn("VMErrorCode::ProgramOverflow", text)
        self.assertIn("uint8_t GetErrorCode() const", text)


if __name__ == "__main__":
    unittest.main()
