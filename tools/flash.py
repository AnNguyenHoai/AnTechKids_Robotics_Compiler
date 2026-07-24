#!/usr/bin/env python3
import subprocess
import sys
import shutil
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def main():
    parser = argparse.ArgumentParser(description="Flash firmware to robot (ESP32)")
    parser.add_argument("--build-dir", required=True, help="Build directory containing program.h")
    parser.add_argument("--port", help="Serial port (e.g., COM5)")
    args = parser.parse_args()

    build_dir = Path(args.build_dir)
    header_src = build_dir / "program.h"
    if not header_src.exists():
        print(f"Header {header_src} not found. Run build first.")
        sys.exit(1)

    platform_dir = ROOT / "robot-platform"
    header_dst = platform_dir / "main" / "src" / "Application" / "generated_program.h"

    # Copy header
    shutil.copy2(header_src, header_dst)
    print(f"Copied header to {header_dst}")

    # Upload
    cmd = ["pio", "run", "-t", "upload", "-d", str(platform_dir)]
    if args.port:
        cmd.extend(["--upload-port", args.port])
    subprocess.check_call(cmd)
    print("Flash complete.")

if __name__ == "__main__":
    main()