#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "tools" / "one_click_production_zip.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("one_click_production_zip", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise AssertionError("Unable to load B2.7 orchestrator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    module = _load_module()

    # Source topology and the no-side-effect plan must remain runnable on CI.
    module._validate_source_layout(ROOT)
    require(module._platform_spec(ROOT) == "espressif32@6.12.0", "B2.7 must consume the exact production ESP32 platform pin")
    result = subprocess.run([sys.executable, str(MODULE_PATH), "--plan"], cwd=ROOT, capture_output=True, text=True)
    require(result.returncode == 0, f"B2.7 --plan failed: {result.stdout}\n{result.stderr}")
    require("Build RoboStudio.exe with PyInstaller" in result.stdout, "plan must include RoboStudio.exe build")
    require("Run B2.6 one-command production builder/finalizer" in result.stdout, "plan must terminate through B2.6")

    # Portable-runtime discovery must require a real interpreter + DLL + stdlib.
    with tempfile.TemporaryDirectory(prefix="b2-7-runtime-") as td:
        runtime = Path(td)
        (runtime / "python.exe").write_bytes(b"exe")
        require(not module._portable_python_valid(runtime), "python.exe alone must not qualify as a portable runtime")
        (runtime / "python310.dll").write_bytes(b"dll")
        (runtime / "python310.zip").write_bytes(b"stdlib")
        require(module._portable_python_valid(runtime), "portable Python topology should be accepted")

    cmd = (ROOT / "BUILD_PRODUCTION_ZIP.cmd").read_text(encoding="utf-8")
    ps1 = (ROOT / "scripts" / "Build-ProductionZip.ps1").read_text(encoding="utf-8")
    requirements = (ROOT / "scripts" / "production-build-requirements.txt").read_text(encoding="utf-8")
    source = MODULE_PATH.read_text(encoding="utf-8")

    require("Build-ProductionZip.ps1" in cmd, "root launcher must delegate to the PowerShell bootstrap")
    require("-3.10" in ps1 and "ROBOSTUDIO_BUILD_PYTHON" in ps1, "PowerShell bootstrap must auto-detect a supported build Python")
    require("pyinstaller" in requirements.lower() and "PySide6" in requirements, "build requirements must prepare the GUI freezer")
    for token in (
        "python-{PYTHON_RUNTIME_VERSION}-embed-amd64.zip",
        "PyInstaller",
        "platformio=={PLATFORMIO_CORE_VERSION}",
        '"platformio", "run"',
        '"esp32dev"',
        '"target_profiles.json"',
        '"one_command_production_build.py"',
        '"RoboStudio-{version}-Windows.zip"',
    ):
        require(token in source, f"B2.7 orchestrator is missing required production stage: {token}")

    print("B2.7 one-click production ZIP gate: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
