#!/usr/bin/env python3
"""Flash a validated Robot Compiler deployment artifact to the ESP32."""
import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.deployment_contract import DeploymentContractError, validate_manifest
from tools.deployment_runtime import (
    DEFAULT_PROCESS_TIMEOUT_SECONDS,
    DeploymentRuntimeError,
    platformio_command,
    run_process,
)


def main():
    parser = argparse.ArgumentParser(description="Flash firmware to robot (ESP32)")
    parser.add_argument("--manifest", required=True, help="H26-M deployment manifest JSON")
    parser.add_argument("--target", default="esp32", help="Expected deployment target")
    parser.add_argument("--port", help="Serial port (e.g., COM5)")
    parser.add_argument("--process-timeout", type=float, default=DEFAULT_PROCESS_TIMEOUT_SECONDS,
                        help="Maximum PlatformIO runtime in seconds")
    args = parser.parse_args()

    if args.process_timeout <= 0:
        parser.error("--process-timeout must be greater than zero")

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
    previous_header = header_dst.read_bytes() if header_dst.is_file() else None

    # Copy only after the complete manifest has passed validation.
    shutil.copy2(header_src, header_dst)
    print(f"Validated deployment manifest for target '{manifest['target']}'.")
    print(f"Copied header to {header_dst}")

    cmd = platformio_command("run", "-t", "upload", "-d", str(platform_dir))
    if args.port:
        cmd.extend(["--upload-port", args.port])
    try:
        print("$", " ".join(cmd), flush=True)
        result = run_process(
            cmd,
            cwd=ROOT,
            timeout=args.process_timeout,
            on_output=lambda line: print(line, end="", flush=True),
        )
    except DeploymentRuntimeError as exc:
        if previous_header is None:
            try:
                header_dst.unlink()
            except FileNotFoundError:
                pass
        else:
            header_dst.write_bytes(previous_header)
        print(f"Deployment failed: {exc}")
        return 1

    if result.returncode != 0:
        if previous_header is None:
            try:
                header_dst.unlink()
            except FileNotFoundError:
                pass
        else:
            header_dst.write_bytes(previous_header)
        print(f"Deployment failed: PlatformIO exited with code {result.returncode}")
        return result.returncode

    print("Flash complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
