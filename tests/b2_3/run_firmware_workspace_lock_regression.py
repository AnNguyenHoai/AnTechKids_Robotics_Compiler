#!/usr/bin/env python3
"""Regression for Windows WinError 32 on reused firmware source workspaces."""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import build_isolation, firmware_workspace, runtime_paths


def check(label: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(label)
    print(f"PASS: {label}")


def make_template(root: Path) -> Path:
    template = root / "robot-platform"
    (template / "main").mkdir(parents=True)
    (template / "platformio.ini").write_text(
        "[env:esp32dev_bootstrap]\nboard = esp32dev\n",
        encoding="utf-8",
    )
    (template / "wifi_config.py").write_text("# fixture\n", encoding="utf-8")
    (template / "main" / "main.cpp").write_text(
        "void setup() {}\nvoid loop() {}\n",
        encoding="utf-8",
    )
    return template


def main() -> int:
    previous_env = os.environ.copy()
    original_rmtree = firmware_workspace.shutil.rmtree
    try:
        with tempfile.TemporaryDirectory(prefix="robostudio-fw-lock-") as tmp:
            base = Path(tmp)
            state = base / "Users" / "EASTVN - An Nguyen" / "AppData" / "Local" / "RoboStudio"
            os.environ[runtime_paths.STATE_ROOT_ENV] = str(state)
            os.environ.pop(runtime_paths.PORTABLE_DATA_ENV, None)
            template = make_template(base)
            project = "bootstrap"
            build_isolation.prepare_build_workspace(project)

            # Reproduce the pre-fix topology from the user's traceback. A stale
            # PlatformIO/esptool descendant may still own a handle below this
            # directory, making shutil.rmtree raise WinError 32 on Windows.
            legacy = build_isolation.build_workspace(project) / "firmware"
            legacy.mkdir(parents=True)
            (legacy / "locked-marker.txt").write_text("legacy workspace", encoding="utf-8")

            def reject_legacy(path, *args, **kwargs):
                candidate = Path(path).expanduser().resolve()
                if candidate == legacy.resolve():
                    raise PermissionError(32, "The process cannot access the file because it is being used by another process", str(candidate))
                return original_rmtree(path, *args, **kwargs)

            firmware_workspace.shutil.rmtree = reject_legacy
            first = firmware_workspace.prepare_firmware_workspace(template, project)
            second = firmware_workspace.prepare_firmware_workspace(template, project)

            check("legacy locked workspace is never deleted before a new run", legacy.is_dir())
            check("first deployment receives a per-run firmware workspace", first.is_dir() and first.name == "firmware")
            check("second deployment receives a different per-run firmware workspace", second.is_dir() and second != first)
            check("per-run workspaces live below platformio/runs", first.parent.parent == build_isolation.build_workspace(project) / firmware_workspace.RUNS_DIRECTORY)

            # Simulate the new run itself remaining locked briefly after the
            # PlatformIO parent process exits. Cleanup must be non-fatal.
            locked_run = first.parent.resolve()

            def reject_first_run(path, *args, **kwargs):
                candidate = Path(path).expanduser().resolve()
                if candidate == locked_run:
                    raise PermissionError(32, "The process cannot access the file because it is being used by another process", str(candidate))
                return original_rmtree(path, *args, **kwargs)

            firmware_workspace.shutil.rmtree = reject_first_run
            check(
                "locked completed run cleanup is deferred instead of failing",
                firmware_workspace.cleanup_firmware_workspace(first, project) is False,
            )

            # Most importantly, the stale locked run cannot block the next
            # deployment because allocation never reuses or removes it.
            third = firmware_workspace.prepare_firmware_workspace(template, project)
            check("next deployment succeeds while previous run is still locked", third.is_dir() and third not in {first, second})

            firmware_workspace.shutil.rmtree = original_rmtree
            check("unlocked run cleanup succeeds", firmware_workspace.cleanup_firmware_workspace(second, project) is True)
            check("new run cleanup succeeds", firmware_workspace.cleanup_firmware_workspace(third, project) is True)

    finally:
        firmware_workspace.shutil.rmtree = original_rmtree
        os.environ.clear()
        os.environ.update(previous_env)

    print("Firmware workspace lock regression: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
