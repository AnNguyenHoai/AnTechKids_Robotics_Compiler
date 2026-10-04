#!/usr/bin/env python3
"""Regression for Windows WinError 32 and reusable student firmware build state."""
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

            # RoboStudio creates a different temporary Python filename on every
            # Run. Those stems must collapse onto one stable PlatformIO project
            # identity so build/libdeps/cache state survives between runs.
            first_alias = "robostudio_first_random_source"
            second_alias = "robostudio_second_random_source"
            first_root = build_isolation.build_root(first_alias)
            second_root = build_isolation.build_root(second_alias)
            check(
                "ephemeral RoboStudio source names share one build root",
                first_root == second_root,
            )
            check(
                "student build root uses the stable project identity",
                first_root.name == build_isolation.STUDENT_PROGRAM_PROJECT_NAME,
            )

            first_env = build_isolation.build_environment(first_alias)
            second_env = build_isolation.build_environment(second_alias)
            for key in (
                build_isolation.PLATFORMIO_BUILD_DIR_ENV,
                build_isolation.PLATFORMIO_LIBDEPS_DIR_ENV,
                build_isolation.PLATFORMIO_CACHE_DIR_ENV,
                build_isolation.PLATFORMIO_BUILD_CACHE_DIR_ENV,
            ):
                check(
                    f"{key} is reused across student Run invocations",
                    first_env[key] == second_env[key],
                )

            check(
                "explicit non-RoboStudio projects remain isolated",
                build_isolation.build_root("lesson-a") != build_isolation.build_root("lesson-b"),
            )

            first_student_run = firmware_workspace.prepare_firmware_workspace(template, first_alias)
            second_student_run = firmware_workspace.prepare_firmware_workspace(template, second_alias)
            check(
                "student firmware source copies remain unique per run",
                first_student_run != second_student_run,
            )
            expected_student_runs = (
                build_isolation.build_workspace(first_alias) / firmware_workspace.RUNS_DIRECTORY
            )
            check(
                "student source runs stay below the shared stable build workspace",
                first_student_run.parent.parent == expected_student_runs
                and second_student_run.parent.parent == expected_student_runs,
            )
            check(
                "first student source run cleanup succeeds",
                firmware_workspace.cleanup_firmware_workspace(first_student_run, first_alias) is True,
            )
            check(
                "second student source run cleanup succeeds",
                firmware_workspace.cleanup_firmware_workspace(second_student_run, second_alias) is True,
            )

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

    print("Firmware workspace lock + incremental cache regression: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
