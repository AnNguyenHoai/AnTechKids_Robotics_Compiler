#!/usr/bin/env python3
"""One-click student program deployment pipeline.

Flow: RoboSim source -> rewrite -> compile -> manifest validation -> firmware
build -> USB or ESP32 OTA upload -> optional health check.

Wi-Fi and OTA credentials are supplied through process arguments or the
ROBOT_WIFI_* / ROBOT_OTA_PASSWORD environment variables. Credentials are
never written to source files or deployment manifests.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLATFORM = ROOT / "robot-platform"
BUILD_ROOT = ROOT / "build"
sys.path.insert(0, str(ROOT))

from tools.deployment_contract import (
    create_manifest, sha256_file, validate_manifest, write_manifest,
)

CAPABILITY_BY_OPCODE = {
    "Forward": "motion.basic", "Backward": "motion.basic", "TurnLeft": "motion.basic", "TurnRight": "motion.basic",
    "SetMotorSpeed": "motion.speed", "MoveInitialize": "motion.encoder_angle", "MoveRunAngle": "motion.encoder_angle",
    "ReadUltrasonic": "sensor.ultrasonic", "ReadTouch": "sensor.touch", "ReadLight": "sensor.light", "ReadColor": "sensor.color", "ReadLine": "sensor.line",
    "GetTraceValue": "sensor.line", "GetTraceState": "sensor.line", "GetTraceRaw": "sensor.line", "GetLightSensorData": "sensor.light",
    "LineBasis": "line.follow", "LineFollow": "line.follow", "LineStop": "line.follow", "LineMillisecond": "line.follow",
    "LineIntersectionStop": "line.follow", "LineTurnEncounterLine": "line.follow", "LineForBmp": "line.follow", "LineSetInitialize": "line.follow",
    "Set3CLed": "actuator.led", "SetLightSensorLed": "actuator.led", "SetServo": "actuator.servo",
    "SetSeeringEngine": "actuator.servo", "SetSeeringEngineTime": "actuator.servo", "SetMotor": "actuator.motor", "SetMotorServo": "actuator.motor", "SetMotorStraightAngle": "actuator.motor",
    "SetMp3Play": "peripheral.mp3", "SetLizard": "peripheral.lizard", "DisplayVariable": "gui.variable",
}


def run(command: list[str], *, env: dict[str, str] | None = None) -> None:
    print("$", " ".join(command))
    subprocess.check_call(command, cwd=ROOT, env=env)


def infer_capabilities(header: Path) -> list[str]:
    text = header.read_text(encoding="utf-8")
    opcodes = set(re.findall(r"Opcode::([A-Za-z0-9_]+)", text))
    capabilities = {"runtime.control"}
    for opcode in opcodes:
        capability = CAPABILITY_BY_OPCODE.get(opcode)
        if capability:
            capabilities.add(capability)
    return sorted(capabilities)


def request_json(url: str, timeout: float) -> dict:
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def wait_for_robot(host: str, timeout: float = 20.0) -> dict:
    deadline = time.monotonic() + timeout
    last_error = None
    while time.monotonic() < deadline:
        try:
            health = request_json(f"http://{host}/api/v1/health", 2.0)
            if health.get("status") == "ok" and health.get("ready") is True:
                return health
            last_error = RuntimeError(f"Robot not ready: {health}")
        except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
            last_error = exc
        time.sleep(0.5)
    raise RuntimeError(f"Robot health check timed out for {host}: {last_error}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Deploy a student RoboSim program in one command")
    parser.add_argument("--input", required=True, help="Student RoboSim .py source")
    parser.add_argument("--mode", choices=("build", "usb", "ota"), default="build")
    parser.add_argument("--port", help="USB serial port for --mode usb")
    parser.add_argument("--robot", help="Robot hostname/IP for --mode ota, e.g. robot-A1B2C3.local")
    parser.add_argument("--ssid", help="Wi-Fi SSID used to build the robot firmware")
    parser.add_argument("--wifi-password", default=None, help="Wi-Fi password; prefer ROBOT_WIFI_PASSWORD")
    parser.add_argument("--ota-password", default=None, help="ArduinoOTA password; prefer ROBOT_OTA_PASSWORD")
    args = parser.parse_args()

    source = Path(args.input).resolve()
    if not source.is_file():
        parser.error(f"Student source not found: {source}")
    if source.suffix.lower() != ".py":
        parser.error("--input must be a .py RoboSim source file")

    wifi_ssid = args.ssid if args.ssid is not None else os.getenv("ROBOT_WIFI_SSID", "")
    wifi_password = args.wifi_password if args.wifi_password is not None else os.getenv("ROBOT_WIFI_PASSWORD", "")
    ota_password = args.ota_password if args.ota_password is not None else os.getenv("ROBOT_OTA_PASSWORD", "")

    if args.mode == "ota":
        if not args.robot or not wifi_ssid:
            parser.error("--mode ota requires --robot and --ssid (or ROBOT_WIFI_SSID)")
        if not ota_password:
            parser.error("--mode ota requires --ota-password or ROBOT_OTA_PASSWORD; no default OTA credential is permitted")

    project_name = source.stem
    build_dir = BUILD_ROOT / project_name
    build_dir.mkdir(parents=True, exist_ok=True)
    rewritten = build_dir / f"{project_name}.rewrite.py"
    header = build_dir / "program.h"
    report = build_dir / "compile_report.json"
    manifest_path = build_dir / "deployment_manifest.json"

    run([sys.executable, str(ROOT / "tools" / "rewrite.py"), "--input", str(source), "--output", str(rewritten)])
    run([sys.executable, str(ROOT / "tools" / "compile.py"), "--input", str(rewritten), "--output", str(header), "--report", str(report)])

    capabilities = infer_capabilities(header)
    platformio_environment = "esp32dev_ota" if args.mode == "ota" else "esp32dev"
    manifest = create_manifest(build_dir, "esp32", capabilities, source_path=source, platformio_environment=platformio_environment)
    manifest_dict = manifest.to_dict()
    write_manifest(manifest, manifest_path)
    validate_manifest(manifest_path, expected_target="esp32")

    platform_header = PLATFORM / "main" / "src" / "Application" / "generated_program.h"
    shutil.copy2(header, platform_header)
    print(f"Validated deployment manifest: {manifest_path}")
    print(f"Capabilities: {', '.join(capabilities)}")

    env = os.environ.copy()
    if wifi_ssid:
        env["ROBOT_WIFI_SSID"] = wifi_ssid
        env["ROBOT_WIFI_PASSWORD"] = wifi_password
    if ota_password:
        env["ROBOT_OTA_PASSWORD"] = ota_password

    if args.mode == "build":
        run(["pio", "run", "-e", "esp32dev"], env=env)
    elif args.mode == "usb":
        command = ["pio", "run", "-e", "esp32dev", "-t", "upload"]
        if args.port:
            command.extend(["--upload-port", args.port])
        run(command, env=env)
    else:
        env["ROBOT_OTA_HOST"] = args.robot
        run(["pio", "run", "-e", "esp32dev_ota", "-t", "upload"], env=env)
        health = wait_for_robot(args.robot)
        print(f"Robot READY: {health.get('hostname')} @ {health.get('ip')}")

    firmware = PLATFORM / ".pio" / "build" / ("esp32dev_ota" if args.mode == "ota" else "esp32dev") / "firmware.bin"
    if firmware.is_file():
        manifest_dict["artifacts"]["firmware"] = {
            "path": str(firmware), "size": firmware.stat().st_size, "sha256": sha256_file(firmware),
        }
        manifest_path.write_text(json.dumps(manifest_dict, indent=2) + "\n", encoding="utf-8")
        print(f"Firmware artifact: {firmware}")

    print("DEPLOYMENT PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
