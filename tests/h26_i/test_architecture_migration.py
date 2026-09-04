from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import architecture_migration_gate as gate


class ArchitectureMigrationTests(unittest.TestCase):
    def test_repository_gate_passes(self):
        report = gate.run_gate()
        self.assertEqual(report["status"], "PASS")
        self.assertFalse(report["allow_legacy_delete"])

    def test_canonical_manifest_matches_generated_opcode_contract(self):
        gate.validate_canonical_isa()

    def test_legacy_reference_in_production_root_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            production = root / "tools"
            production.mkdir()
            (production / "bad.py").write_text(
                "# forbidden reference\nfrom packages.robot-common import Opcode\n",
                encoding="utf-8",
            )

            manifest = {
                "production_scan_roots": ["tools"],
                "legacy_components": [
                    {
                        "path": "legacy/Opcode.h",
                        "status": "legacy-isolated",
                        "retirement": "blocked-until-equivalence",
                        "forbidden_production_tokens": ["robot-common"],
                    }
                ],
            }

            original_root = gate.ROOT
            try:
                gate.ROOT = root
                with self.assertRaises(gate.MigrationGateError):
                    gate.validate_legacy_isolation(manifest)
            finally:
                gate.ROOT = original_root

    def test_delete_policy_cannot_be_enabled(self):
        manifest = {
            "retirement_policy": {
                "allow_delete": True,
                "required_evidence": [
                    "canonical semantic equivalence",
                    "unified E2E oracle pass",
                    "firmware build pass",
                    "physical validation gate",
                ],
            },
            "legacy_components": [],
        }
        with self.assertRaises(gate.MigrationGateError):
            gate.validate_retirement_policy(manifest)


if __name__ == "__main__":
    unittest.main()
