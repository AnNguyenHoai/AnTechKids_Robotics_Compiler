"""RSD-06 packaged distribution preflight checks."""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import runtime_paths, runtime_preflight, runtime_resources


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"PASS: {name}")


def expect_error(name: str, fn, expected: str) -> None:
    try:
        fn()
    except runtime_preflight.RuntimePreflightError as exc:
        check(name, expected in str(exc))
    else:
        raise AssertionError(f"{name}: validation unexpectedly succeeded")


def make_distribution(root: Path) -> None:
    python = root / runtime_preflight._python_relative_path()
    python.parent.mkdir(parents=True, exist_ok=True)
    python.write_bytes(b"portable-python")

    core = root / runtime_preflight.RUNTIME_PLATFORMIO
    (core / "platforms" / "espressif32").mkdir(parents=True)
    (core / "packages" / "tool-esptoolpy").mkdir(parents=True)
    manifest = {
        "schema": "antechkids.robostudio.deployment-runtime",
        "schema_version": 1,
        "platformio_core": {
            "source_not_embedded": True,
            "required_directories": ["platforms", "packages"],
            "file_count": 0,
        },
        "runtime_layout": {
            "core_dir": "runtime/platformio",
            "python": "runtime/bin/python.exe" if sys.platform == "win32" else "runtime/bin/python",
            "platformio_module": "platformio",
        },
        "portable_python_required": True,
        "host_virtualenv_included": False,
    }
    (core / "deployment-runtime.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )

    resources = root / runtime_preflight.RUNTIME_RESOURCES
    profile = resources / runtime_resources.RESOURCE_SPECS["target_profiles"]
    profile.parent.mkdir(parents=True, exist_ok=True)
    profile.write_text("{\"targets\": []}\n", encoding="utf-8")
    runtime_resources.write_resource_manifest(resources)


def main() -> int:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp) / "RoboStudio"
        root.mkdir()
        make_distribution(root)

        with patch_environment(root):
            report = runtime_preflight.validate_distribution(root)
            check("complete distribution passes preflight", report.application_root == root)
            check("preflight resolves portable Python under app root", report.python == root / runtime_preflight._python_relative_path())
            check("preflight resolves PlatformIO under app root", report.platformio == root / "runtime" / "platformio")
            check("preflight resolves resources under app root", report.resources == root / "runtime" / "resources")

            (root / runtime_preflight.RUNTIME_BIN / runtime_preflight._python_relative_path().name).unlink()
            expect_error("missing portable Python is rejected", lambda: runtime_preflight.validate_distribution(root), "missing portable Python")
            make_distribution(root)

            penv = root / "runtime" / "platformio" / "penv"
            penv.mkdir()
            expect_error("host-specific penv is rejected", lambda: runtime_preflight.validate_distribution(root), "host-specific penv")
            penv.rmdir()

            manifest_path = root / "runtime" / "platformio" / "deployment-runtime.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["portable_python_required"] = False
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            expect_error("invalid deployment manifest is rejected", lambda: runtime_preflight.validate_distribution(root), "must require portable Python")
            make_distribution(root)

            profile = root / "runtime" / "resources" / "robot-isa" / "target_profiles.json"
            profile.write_text("tampered\n", encoding="utf-8")
            expect_error("resource checksum drift is rejected", lambda: runtime_preflight.validate_distribution(root), "checksum mismatch")

    print("RSD-06 distribution preflight checks: PASS")
    return 0


class patch_environment:
    """Temporarily bind ROBOSTUDIO_HOME to the distribution under test."""

    def __init__(self, root: Path):
        self.root = root
        self.previous = os.environ.get(runtime_paths.APPLICATION_HOME_ENV)

    def __enter__(self):
        os.environ[runtime_paths.APPLICATION_HOME_ENV] = str(self.root)
        return self

    def __exit__(self, exc_type, exc, tb):
        if self.previous is None:
            os.environ.pop(runtime_paths.APPLICATION_HOME_ENV, None)
        else:
            os.environ[runtime_paths.APPLICATION_HOME_ENV] = self.previous
        return False


if __name__ == "__main__":
    raise SystemExit(main())
