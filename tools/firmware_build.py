#!/usr/bin/env python3
"""Build ESP32 firmware from a compiled RoboSim program artifact.

H26-H is an additive integration layer. It makes the previously implicit
program.h -> generated_program.h -> PlatformIO build step explicit while
leaving the existing compiler, VM, firmware sources, and upload flow intact.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable, Sequence

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PROJECT = ROOT / "robot-platform"
DEFAULT_ENV = "esp32dev"


def find_platformio() -> list[str]:
    """Resolve PlatformIO without assuming the CLI is globally installed."""
    pio = shutil.which("pio")
    if pio:
        return [pio]
    return [sys.executable, "-m", "platformio"]


def build_command(project_dir: Path, environment: str) -> list[str]:
    """Return a build-only command; upload is deliberately never requested."""
    return find_platformio() + ["run", "-d", str(project_dir), "-e", environment]


def display_path(path: Path) -> str:
    """Use repo-relative paths when possible, otherwise return the full path."""
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def locate_firmware_artifacts(project_dir: Path, environment: str) -> list[str]:
    candidates = (
        project_dir / ".pio" / "build" / environment / "firmware.bin",
        project_dir / ".pio" / "build" / environment / "firmware.elf",
    )
    return [display_path(path) for path in candidates if path.exists()]


def build_firmware(
    program_header: Path,
    *,
    project_dir: Path = DEFAULT_PROJECT,
    environment: str = DEFAULT_ENV,
    report_path: Path | None = None,
    runner: Callable[[Sequence[str], Path], int] | None = None,
) -> dict:
    """Stage ``program.h`` into firmware and perform a PlatformIO build.

    The generated firmware header is restored after the build. This keeps the
    integration usable from regression runs without leaving source-tree
    mutations behind.
    """
    program_header = program_header.resolve()
    project_dir = project_dir.resolve()
    target_header = project_dir / "main" / "src" / "Application" / "generated_program.h"

    if not program_header.is_file():
        raise FileNotFoundError(f"Program header not found: {program_header}")
    if not project_dir.is_dir():
        raise FileNotFoundError(f"Firmware project not found: {project_dir}")
    if not target_header.parent.is_dir():
        raise FileNotFoundError(f"Firmware application directory not found: {target_header.parent}")

    original = target_header.read_bytes() if target_header.exists() else None
    command = build_command(project_dir, environment)
    runner = runner or (lambda cmd, cwd: subprocess.call(cmd, cwd=cwd))
    return_code = 1
    try:
        shutil.copy2(program_header, target_header)
        return_code = int(runner(command, ROOT))
    finally:
        if original is None:
            target_header.unlink(missing_ok=True)
        else:
            target_header.write_bytes(original)

    report = {
        "task": "H26-H",
        "status": "PASS" if return_code == 0 else "FAIL",
        "project": display_path(project_dir),
        "environment": environment,
        "input_header": display_path(program_header),
        "target_header": display_path(target_header),
        "command": command,
        "upload": False,
        "artifacts": locate_firmware_artifacts(project_dir, environment) if return_code == 0 else [],
        "return_code": return_code,
    }
    if report_path is not None:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if return_code != 0:
        raise subprocess.CalledProcessError(return_code, command)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Build ESP32 firmware from program.h without uploading")
    parser.add_argument("--program-header", required=True, help="Compiled program.h artifact")
    parser.add_argument("--project-dir", default=str(DEFAULT_PROJECT), help="PlatformIO project directory")
    parser.add_argument("--environment", default=DEFAULT_ENV, help="PlatformIO environment")
    parser.add_argument("--report", help="Optional JSON report path")
    args = parser.parse_args()

    try:
        report = build_firmware(
            Path(args.program_header),
            project_dir=Path(args.project_dir),
            environment=args.environment,
            report_path=Path(args.report) if args.report else None,
        )
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        print(f"H26-H firmware build failed: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(report, indent=2, sort_keys=True))
    print("H26-H firmware build: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
