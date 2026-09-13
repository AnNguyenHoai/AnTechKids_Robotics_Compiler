"""RSD-21.5 production RoboStudio + Compiler E2E contract regression suite."""
from __future__ import annotations

import json
import sys
import tempfile
import zipfile
from pathlib import Path
import sys

# This test is intentionally executable directly from the repository root:
#   python tests\\rsd_21_5\\run_rsd_21_5.py
# Python puts tests/rsd_21_5 on sys.path for that invocation, not the repository
# root. Add the repository root before importing project packages.
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import production_e2e


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"PASS: {name}")


def _make_test_artifact(root: Path) -> tuple[Path, Path]:
    """Create a minimal production-shaped artifact for the E2E contract test."""
    package = root / "package"
    package.mkdir()
    app = package / "RoboStudio.exe"
    # The fixture is intentionally a Python-backed executable so this regression
    # suite can exercise the real extraction/process boundary on every developer
    # machine without requiring the production Windows binary or PlatformIO.
    app.write_text(
        "import pathlib, sys\n"
        "args=sys.argv[1:]\n"
        "if '--self-test' in args:\n"
        "    print('ROBOSTUDIO_E2E_READY')\n"
        "    raise SystemExit(0)\n"
        "if '--compile' in args:\n"
        "    out=pathlib.Path(args[args.index('--output')+1])\n"
        "    out.parent.mkdir(parents=True, exist_ok=True)\n"
        "    out.write_bytes(b'ROBOT_BYTECODE_E2E_OK\\n')\n"
        "    print('COMPILE_OK')\n"
        "    raise SystemExit(0)\n"
        "raise SystemExit(2)\n",
        encoding="utf-8",
    )
    resources = package / "runtime" / "resources"
    resources.mkdir(parents=True)
    (resources / "target_profiles.json").write_text('{"targets": []}\n', encoding="utf-8")

    artifact = root / "production.zip"
    with zipfile.ZipFile(artifact, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(package.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(package).as_posix())

    source = root / "sample.py"
    source.write_text("forward(50)\nwait(100)\nstop()\n", encoding="utf-8")
    return artifact, source


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="rsd-21-5-test-") as td:
        root = Path(td)
        artifact, source = _make_test_artifact(root)

        result = production_e2e.evaluate_production_artifact(
            artifact=artifact,
            source=source,
            launch=True,
            launch_command=[sys.executable, "{app}", "--self-test"],
            compile_command=[
                sys.executable,
                "{app}",
                "--compile",
                "{source}",
                "--output",
                "{output}",
            ],
        )
        report = result.to_dict()
        names = set(zipfile.ZipFile(artifact).namelist())

        check("production artifact exists", artifact.is_file())
        check("E2E report is JSON serializable", bool(json.dumps(report)))
        check("E2E status is PASS", report["status"] == "PASS")
        check("target machine prerequisites remain external", report["target_machine_prerequisites"] is True)
        check("source tree is not executed", report["source_tree_execution"] is False)
        check("RoboStudio starts from extracted artifact", report["robostudio_started"] is True)
        check("compiler executes from extracted artifact", report["compiler_succeeded"] is True)
        check("extraction root is recorded", bool(report["extracted_root"]))
        check("RoboStudio executable is recorded", report["evidence"]["robostudio"] == "RoboStudio.exe")
        check("artifact contains RoboStudio", "RoboStudio.exe" in names)
        check("artifact contains runtime resources", "runtime/resources/target_profiles.json" in names)
        check("artifact does not bundle Python", not any("python" in name.lower() for name in names))
        check("artifact does not bundle PlatformIO", not any("platformio" in name.lower() for name in names))

    print("RSD-21.5 RoboStudio + Compiler E2E checks: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
