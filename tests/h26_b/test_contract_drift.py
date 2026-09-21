#!/usr/bin/env python3
"""H26-B tests.

These tests intentionally characterize the current production contracts. They
must fail loudly when a future refactor changes a protected boundary without
an explicit baseline update.
"""

from __future__ import annotations

import re
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
        self.assertRegex(baseline.get("baseline_commit", ""), r"^[0-9a-f]{40}$")
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

    def test_protected_file_hashes_are_owned_by_baseline(self):
        baseline = checker.load_baseline(checker.BASELINE_PATH)
        protected = baseline.get("protected_files", {})
        self.assertIsInstance(protected, dict)
        self.assertTrue(protected, "H26-B baseline must protect at least one production file")
        for raw_path, expected_sha in protected.items():
            self.assertRegex(expected_sha, r"^[0-9a-f]{40}$")
            path = ROOT / raw_path
            self.assertTrue(path.is_file(), f"Protected baseline file is missing: {raw_path}")
            self.assertEqual(
                checker.git_blob_sha(checker.read_text(path)),
                expected_sha,
                f"Protected baseline drifted: {raw_path}",
            )


if __name__ == "__main__":
    unittest.main()
