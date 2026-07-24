#!/usr/bin/env python3
"""
Build and optionally flash all physical test programs.
"""
import subprocess
import sys
import json
import shutil
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PHYSICAL_DIR = ROOT / "examples" / "physical"
BUILD_ROOT = ROOT / "build" / "physical"
PLATFORM_HEADER = ROOT / "robot-platform" / "main" / "src" / "Application" / "generated_program.h"


def main():
    parser = argparse.ArgumentParser(description="Build all physical test programs")
    parser.add_argument("--flash", action="store_true", help="Flash after building")
    parser.add_argument("--port", help="Serial port for flashing (e.g., COM5)")
    parser.add_argument("--skip-firmware", action="store_true", help="Skip firmware build")
    args = parser.parse_args()

    BUILD_ROOT.mkdir(parents=True, exist_ok=True)

    results = {}
    for py_file in sorted(PHYSICAL_DIR.glob("*.py")):
        name = py_file.stem
        print(f"\n=== Building {name} ===")
        build_dir = BUILD_ROOT / name
        build_dir.mkdir(parents=True, exist_ok=True)

        # 1. Rewrite
        rewrite_output = build_dir / f"{name}.rewrite.py"
        cmd_rewrite = [
            sys.executable,
            str(ROOT / "tools" / "rewrite.py"),
            "--input", str(py_file),
            "--output", str(rewrite_output)
        ]
        subprocess.run(cmd_rewrite, check=True)
        results[name] = {"rewrite": "PASS"}

        # 2. Compile
        header_output = build_dir / "program.h"
        report_output = build_dir / "compile_report.json"
        cmd_compile = [
            sys.executable,
            str(ROOT / "tools" / "compile.py"),
            "--input", str(rewrite_output),
            "--output", str(header_output),
            "--report", str(report_output)
        ]
        subprocess.run(cmd_compile, check=True)
        results[name]["compile"] = "PASS"

        # 3. Copy header to platform
        shutil.copy2(header_output, PLATFORM_HEADER)
        results[name]["copy_header"] = "PASS"

        # 4. Firmware build (optional)
        if not args.skip_firmware:
            print("Building firmware...")
            # Use python -m platformio to ensure correct Python environment
            cmd_build = [
                sys.executable, "-m", "platformio",
                "run", "-d", str(ROOT / "robot-platform")
            ]
            subprocess.run(cmd_build, check=True)
            results[name]["firmware_build"] = "PASS"
        else:
            results[name]["firmware_build"] = "SKIPPED"

        # 5. Flash (optional)
        if args.flash:
            print("Flashing...")
            cmd_flash = [
                sys.executable, "-m", "platformio",
                "run", "-t", "upload", "-d", str(ROOT / "robot-platform")
            ]
            if args.port:
                cmd_flash.extend(["--upload-port", args.port])
            subprocess.run(cmd_flash, check=True)
            results[name]["flash"] = "PASS"
        else:
            results[name]["flash"] = "SKIPPED"

    # Save summary
    summary_path = BUILD_ROOT / "physical_build_summary.json"
    with open(summary_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSummary saved to {summary_path}")


if __name__ == "__main__":
    main()