import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

from firmware_build import build_command, build_firmware


class FirmwareBuildIntegrationTests(unittest.TestCase):
    def _make_project(self, root: Path) -> tuple[Path, Path, Path]:
        project = root / "robot-platform"
        app = project / "main" / "src" / "Application"
        app.mkdir(parents=True)
        target = app / "generated_program.h"
        target.write_text("ORIGINAL", encoding="utf-8")
        header = root / "program.h"
        header.write_text("GENERATED", encoding="utf-8")
        return project, target, header

    def test_build_command_never_requests_upload(self):
        command = build_command(Path("robot-platform"), "esp32dev")
        self.assertIn("run", command)
        self.assertIn("esp32dev", command)
        self.assertNotIn("upload", command)
        self.assertNotIn("-t", command)

    def test_stages_header_builds_and_restores_source_header(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project, target, header = self._make_project(root)
            report_path = root / "report.json"
            calls = []

            def fake_runner(command, cwd):
                calls.append((list(command), cwd))
                self.assertEqual(target.read_text(encoding="utf-8"), "GENERATED")
                return 0

            report = build_firmware(
                header,
                project_dir=project,
                environment="testenv",
                report_path=report_path,
                runner=fake_runner,
            )

            self.assertEqual(report["status"], "PASS")
            self.assertFalse(report["upload"])
            self.assertEqual(report["environment"], "testenv")
            self.assertEqual(target.read_text(encoding="utf-8"), "ORIGINAL")
            self.assertEqual(len(calls), 1)
            saved = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(saved["task"], "H26-H")
            self.assertEqual(saved["return_code"], 0)

    def test_build_failure_restores_source_header(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project, target, header = self._make_project(root)

            def fake_runner(command, cwd):
                self.assertEqual(target.read_text(encoding="utf-8"), "GENERATED")
                return 7

            with self.assertRaises(Exception) as ctx:
                build_firmware(header, project_dir=project, runner=fake_runner)

            self.assertEqual(getattr(ctx.exception, "returncode", None), 7)
            self.assertEqual(target.read_text(encoding="utf-8"), "ORIGINAL")

    def test_missing_program_header_fails_before_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project, target, _ = self._make_project(root)
            runner = Mock(return_value=0)
            with self.assertRaises(FileNotFoundError):
                build_firmware(root / "missing.h", project_dir=project, runner=runner)
            runner.assert_not_called()


if __name__ == "__main__":
    unittest.main()
