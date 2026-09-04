#!/usr/bin/env python3
"""H26-B tests.

These tests intentionally characterize the current production contracts. They
must fail loudly when a future refactor changes a protected boundary without
an explicit baseline update.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import check_contract_drift as checker  # noqa: E402


class TestContractDrift(unittest.TestCase):
    def test_current_baseline_has_no_unexpected_drift(self):
        findings, baseline = checker.run()
        errors = [item for item in findings if item.severity == "ERROR"]
        self.assertEqual(baseline["baseline_commit"], "9d14e8941b2ea8bacc429c7118feb2a37001dc97")
        self.assertEqual(errors, [], msg="; ".join(item.message for item in errors))

    def test_registry_is_backed_by_generated_opcode_contract(self):
        opcode_path = ROOT / "robot-compiler" / "compiler" / "generated" / "opcode.py"
        registry_path = ROOT / "robot-compiler" / "compiler" / "generated" / "function_registry.py"
        opcodes = checker.parse_opcode_values(checker.read_text(opcode_path))
        registry = checker.parse_registry_opcodes(checker.read_text(registry_path))
        self.assertTrue(registry)
        self.assertTrue(opcodes)
        self.assertEqual(sorted(set(registry.values()) - set(opcodes)), [])

    def test_generated_opcode_values_are_unique(self):
        opcode_path = ROOT / "robot-compiler" / "compiler" / "generated" / "opcode.py"
        opcodes = checker.parse_opcode_values(checker.read_text(opcode_path))
        values = list(opcodes.values())
        self.assertEqual(len(values), len(set(values)))

    def test_golden_corpus_exists(self):
        golden_dir = ROOT / "robot-platform" / "golden"
        programs = list(golden_dir.glob("*.py"))
        self.assertTrue(programs, "Golden program corpus must not be empty")

    def test_git_blob_sha_matches_known_sample(self):
        path = ROOT / "tools" / "build.py"
        self.assertEqual(
            checker.git_blob_sha(checker.read_text(path)),
            "a4de23ac985c498439bd91e4d7f99dd87d4e3023",
        )


if __name__ == "__main__":
    unittest.main()
