from __future__ import annotations

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

    def test_legacy_component_self_reference_is_ignored(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            legacy_dir = root / "robot-compiler" / "compiler"
            legacy_dir.mkdir(parents=True)
            (legacy_dir / "compiler.cpp").write_text('#include "compiler.h"\n', encoding="utf-8")
            (legacy_dir / "compiler.h").write_text("#pragma once\n", encoding="utf-8")

            manifest = {
                "production_scan_roots": ["robot-compiler"],
                "legacy_components": [
                    {
                        "path": "robot-compiler/compiler/compiler.cpp",
                        "status": "legacy-isolated",
                        "retirement": "blocked-until-equivalence",
                        "forbidden_production_tokens": ["compiler.cpp", "compiler.h"],
                    },
                    {
                        "path": "robot-compiler/compiler/compiler.h",
                        "status": "legacy-isolated",
                        "retirement": "blocked-until-equivalence",
                        "forbidden_production_tokens": ["compiler.cpp", "compiler.h"],
                    },
                ],
            }

            original_root = gate.ROOT
            try:
                gate.ROOT = root
                gate.validate_legacy_isolation(manifest)
            finally:
                gate.ROOT = original_root

    def test_legacy_include_from_production_root_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            compiler_dir = root / "robot-compiler" / "compiler"
            compiler_dir.mkdir(parents=True)
            (compiler_dir / "compiler.h").write_text("#pragma once\n", encoding="utf-8")
            (compiler_dir / "production.cpp").write_text(
                '#include "compiler.h"\nint run() { return 0; }\n',
                encoding="utf-8",
            )

            manifest = {
                "production_scan_roots": ["robot-compiler"],
                "legacy_components": [
                    {
                        "path": "robot-compiler/compiler/compiler.h",
                        "status": "legacy-isolated",
                        "retirement": "blocked-until-equivalence",
                        "forbidden_production_tokens": ["compiler.h"],
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

    def test_filename_text_without_dependency_is_allowed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            tools = root / "tools"
            tools.mkdir()
            (tools / "note.py").write_text(
                "legacy filename: compiler.h\n",
                encoding="utf-8",
            )

            manifest = {
                "production_scan_roots": ["tools"],
                "legacy_components": [
                    {
                        "path": "legacy/compiler.h",
                        "status": "legacy-isolated",
                        "retirement": "blocked-until-equivalence",
                        "forbidden_production_tokens": ["compiler.h"],
                    }
                ],
            }

            original_root = gate.ROOT
            try:
                gate.ROOT = root
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
