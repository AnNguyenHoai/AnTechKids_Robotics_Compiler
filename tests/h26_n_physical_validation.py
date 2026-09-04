import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.deployment_contract import create_manifest, write_manifest
from tools.physical_validation import PhysicalValidationError, validate_deployment


class PhysicalValidationTests(unittest.TestCase):
    def test_preflight_accepts_matching_deployment_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            build = Path(tmp) / "build"
            build.mkdir()
            source = ROOT / "robot-platform" / "main" / "src" / "Application" / "generated_program.h"
            program = build / "program.h"
            program.write_bytes(source.read_bytes())
            manifest = create_manifest(build, "esp32", ())
            manifest_path = write_manifest(manifest, build / "deployment_manifest.json")
            report = validate_deployment(manifest_path)
            self.assertTrue(report["checks"]["deployment_manifest_valid"])
            self.assertTrue(report["checks"]["generated_program_matches_manifest_artifact"])
            self.assertTrue(report["physical_validation_required"])
            self.assertFalse(report["checks"]["physical_device_connected"])

    def test_preflight_rejects_generated_program_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            build = Path(tmp) / "build"
            build.mkdir()
            program = build / "program.h"
            program.write_text("const Instruction generatedProgram[] = {};\nconst uint16_t generatedProgramSize = 0;\n", encoding="utf-8")
            manifest_path = write_manifest(create_manifest(build, "esp32", ()), build / "deployment_manifest.json")
            with self.assertRaisesRegex(PhysicalValidationError, "does not match"):
                validate_deployment(manifest_path)

    def test_preflight_rejects_incomplete_generated_program(self):
        with tempfile.TemporaryDirectory() as tmp:
            build = Path(tmp) / "build"
            build.mkdir()
            program = build / "program.h"
            program.write_text("const Instruction generatedProgram[] = {};\n", encoding="utf-8")
            manifest_path = write_manifest(create_manifest(build, "esp32", ()), build / "deployment_manifest.json")
            original = ROOT / "robot-platform" / "main" / "src" / "Application" / "generated_program.h"
            backup = original.read_bytes()
            try:
                original.write_text("const Instruction generatedProgram[] = {};\n", encoding="utf-8")
                with self.assertRaisesRegex(PhysicalValidationError, "incomplete"):
                    validate_deployment(manifest_path)
            finally:
                original.write_bytes(backup)


if __name__ == "__main__":
    unittest.main(verbosity=2)
