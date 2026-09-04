#!/usr/bin/env python3
"""Flash a validated Robot Compiler deployment artifact to the ESP32."""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.deployment_contract import DeploymentContractError, validate_manifest


def main():
    parser = argparse.ArgumentParser(description="Flash firmware to robot (ESP32)")
    parser.add_argument("--manifest", required=True, help="H26-M deployment manifest JSON")
    parser.add_argument("--target", default="esp32", help="Expected deployment target")
    parser.add_argument("--port", help="Serial port (e.g., COM5)")
    args = parser.parse_args()

    try:
        manifest = validate_manifest(Path(args.manifest), expected_target=args.target)
    except DeploymentContractError as exc:
        print(f"Deployment blocked: {exc}")
        return 1

    # Keep the legacy build-artifact boundary explicit: the validated manifest
    # identifies the build directory and its program.h artifact.
    build_dir = Path(manifest["artifacts"]["program_header"]["path"]).parent
    header_src = build_dir / "program.h"
    if header_src != Path(manifest["artifacts"]["program_header"]["path"]):
        print("Deployment blocked: manifest program_header path is invalid.")
        return 1

    platform_dir = ROOT / "robot-platform"
    header_dst = platform_dir / "main" / "src" / "Application" / "generated_program.h"

    # Copy only after the complete manifest has passed validation.
    shutil.copy2(header_src, header_dst)
    print(f"Validated deployment manifest for target '{manifest['target']}'.")
    print(f"Copied header to {header_dst}")

    cmd = ["pio", "run", "-t", "upload", "-d", str(platform_dir)]
    if args.port:
        cmd.extend(["--upload-port", args.port])
    subprocess.check_call(cmd)
    print("Flash complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
