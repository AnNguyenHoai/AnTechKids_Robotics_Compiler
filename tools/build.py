#!/usr/bin/env python3
import subprocess
import sys
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Build RoboSim program from source to header")
    parser.add_argument("--input", required=True, help="RoboSim source .py")
    parser.add_argument("--output", help="Header output (optional)")
    parser.add_argument("--build-dir", help="Build directory (optional)")
    parser.add_argument("--copy", action="store_true", help="Copy header to robot-platform after build")
    parser.add_argument("--target", default="esp32", help="Compile target profile (default: esp32)")
    args = parser.parse_args()

    input_path = Path(args.input)
    if args.build_dir:
        build_dir = Path(args.build_dir)
    else:
        build_dir = ROOT / "build" / input_path.stem
    build_dir.mkdir(parents=True, exist_ok=True)

    rewrite_script = ROOT / "tools" / "rewrite.py"
    compile_script = ROOT / "tools" / "compile.py"

    rewrite_output = build_dir / f"{input_path.stem}.rewrite.py"
    header_output = build_dir / "program.h"
    report_output = build_dir / "compile_report.json"

    # Rewrite
    subprocess.check_call([
        sys.executable,
        str(rewrite_script),
        "--input",
        str(input_path),
        "--output",
        str(rewrite_output),
    ])
    # Compile
    subprocess.check_call([
        sys.executable,
        str(compile_script),
        "--input",
        str(rewrite_output),
        "--output",
        str(header_output),
        "--report",
        str(report_output),
        "--target",
        args.target,
    ])

    if args.copy:
        platform_header = ROOT / "robot-platform" / "main" / "src" / "Application" / "generated_program.h"
        shutil.copy2(header_output, platform_header)
        print(f"Copied header to {platform_header}")

    print(
        f"Build completed for target '{args.target}'. "
        f"Header: {header_output}, Report: {report_output}"
    )

if __name__ == "__main__":
    main()
