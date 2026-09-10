#!/usr/bin/env python3
"""One-click student program deployment pipeline.

Flow: RoboSim source -> rewrite -> compile -> manifest validation -> firmware
build -> USB or HTTP OTA upload -> health check.

The firmware keeps ArduinoOTA for compatibility/recovery, while RoboStudio uses
an HTTP OTA endpoint so deployment does not depend on espota's UDP invitation
and host-side listener. This is more reliable on classroom Windows networks.

The ``bootstrap`` mode is the first-flash path: a RoboStudio-generated local
artifact is consumed by PlatformIO and stored by the firmware in ESP32 NVS.
Bootstrap artifacts and credentials are never written into the repository.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import shutil
import socket
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLATFORM = ROOT / "robot-platform"
BUILD_ROOT = ROOT / "build"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.deployment_contract import (
    create_manifest, sha256_file, validate_manifest, write_manifest,
)
from tools.deployment_runtime import (
    DEFAULT_PROCESS_TIMEOUT_SECONDS,
    DeploymentRuntimeError,
    deployment_runtime_environment,
    platformio_command,
    run_process,
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


def run(command: list[str], *, env: dict[str, str] | None = None, cwd: Path = ROOT,
        timeout: float = DEFAULT_PROCESS_TIMEOUT_SECONDS) -> None:
    """Run a deployment command with live output and a bounded runtime."""
    print("$", " ".join(command), flush=True)
    try:
        result = run_process(command, cwd=cwd, env=env, timeout=timeout,
                             on_output=lambda line: print(line, end="", flush=True))
    except DeploymentRuntimeError as exc:
        raise RuntimeError(str(exc)) from exc
    if result.returncode != 0:
        raise RuntimeError(f"Command failed with exit code {result.returncode}: {' '.join(command)}")


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
    import urllib.request
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def normalize_robot_host(host: str) -> str:
    """Validate and normalize the hostname/IP accepted by the HTTP OTA client."""
    value = (host or "").strip()
    if not value:
        raise ValueError("Robot host is required.")
    if "://" in value or "/" in value or "\\" in value:
        raise ValueError("Robot host must be a hostname or IP address, not a URL/path.")
    if len(value) > 253:
        raise ValueError("Robot host is too long.")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.-]*", value):
        raise ValueError("Robot host contains unsupported characters.")
    return value


def wait_for_robot(host: str, timeout: float = 30.0, poll_interval: float = 0.5) -> dict:
    """Wait for a robot health endpoint to become ready after deployment."""
    host = normalize_robot_host(host)
    if timeout <= 0:
        raise ValueError("Robot verification timeout must be greater than zero.")
    deadline = time.monotonic() + timeout
    last_error = None
    while time.monotonic() < deadline:
        try:
            health = request_json(f"http://{host}/api/v1/health", 2.0)
            if health.get("status") == "ok" and health.get("ready") is True:
                return health
            last_error = RuntimeError(f"Robot not ready: {health}")
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            last_error = exc
        time.sleep(min(poll_interval, max(0.0, deadline - time.monotonic())))
    raise RuntimeError(f"Robot health check timed out for {host}: {last_error}")


def validate_bootstrap_config(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Invalid bootstrap config: {exc}") from exc
    if data.get("type") != "antechkids.robot.bootstrap":
        raise RuntimeError("Unsupported robot bootstrap config type")
    if data.get("schema_version") != 1:
        raise RuntimeError("Unsupported robot bootstrap schema version")
    wifi = data.get("wifi")
    ota = data.get("ota")
    if not isinstance(wifi, dict) or not str(wifi.get("ssid", "")).strip():
        raise RuntimeError("Bootstrap config requires a Wi-Fi SSID")
    if not isinstance(ota, dict) or not str(ota.get("password", "")):
        raise RuntimeError("Bootstrap config requires an OTA password")
    return data


def flash_bootstrap(config_path: Path, port: str | None) -> int:
    config = validate_bootstrap_config(config_path.resolve())
    env = deployment_runtime_environment(os.environ.copy())
    env["ROBOT_BOOTSTRAP_CONFIG"] = str(config_path.resolve())
    env["ROBOT_WIFI_SSID"] = str(config["wifi"]["ssid"])
    env["ROBOT_WIFI_PASSWORD"] = str(config["wifi"].get("password", ""))
    env["ROBOT_OTA_PASSWORD"] = str(config["ota"]["password"])

    command = platformio_command("run", "-e", "esp32dev_bootstrap", "-t", "upload")
    if port:
        command.extend(["--upload-port", port])
    run(command, cwd=PLATFORM, env=env)
    print("FIRST-FLASH BOOTSTRAP PASS")
    print("Wi-Fi bootstrap data embedded for NVS provisioning on first boot.")
    return 0


def http_ota_upload(host: str, password: str, firmware: Path, timeout: float = 180.0) -> str:
    """Upload firmware using the robot's HTTP OTA endpoint.

    The firmware image is streamed in bounded chunks. The timeout is a total
    transport deadline rather than an unbounded per-socket-operation wait.
    """
    host = normalize_robot_host(host)
    if not password:
        raise RuntimeError("HTTP OTA requires the robot OTA password")
    if not firmware.is_file():
        raise RuntimeError(f"Firmware image not found: {firmware}")
    image_size = firmware.stat().st_size
    if image_size <= 0:
        raise RuntimeError(f"Firmware image is empty: {firmware}")

    boundary = "----AnTechKidsRoboStudioOTA" + f"{int(time.time() * 1000):x}"
    filename = firmware.name
    preamble = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="firmware"; filename="{filename}"\r\n'
        "Content-Type: application/octet-stream\r\n"
        "\r\n"
    ).encode("ascii")
    closing = f"\r\n--{boundary}--\r\n".encode("ascii")
    total_length = len(preamble) + image_size + len(closing)
    auth = base64.b64encode(f"robot:{password}".encode("utf-8")).decode("ascii")

    print(f"HTTP OTA target: {host}:80")
    print(f"HTTP OTA image: {firmware} ({image_size} bytes)")

    from http.client import HTTPConnection

    deadline = time.monotonic() + timeout
    connection = HTTPConnection(host, 80, timeout=min(10.0, timeout))
    started = time.monotonic()
    try:
        connection.connect()

        def refresh_socket_timeout() -> None:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("HTTP OTA transport deadline exceeded")
            if connection.sock is not None:
                connection.sock.settimeout(min(10.0, remaining))

        refresh_socket_timeout()
        connection.putrequest("POST", "/api/v1/ota")
        connection.putheader("Authorization", f"Basic {auth}")
        connection.putheader("Content-Type", f"multipart/form-data; boundary={boundary}")
        connection.putheader("Content-Length", str(total_length))
        connection.putheader("Connection", "close")
        connection.endheaders()
        refresh_socket_timeout()
        connection.send(preamble)

        sent = 0
        with firmware.open("rb") as stream:
            while True:
                chunk = stream.read(8192)
                if not chunk:
                    break
                refresh_socket_timeout()
                connection.send(chunk)
                sent += len(chunk)
                if sent == image_size or sent % (256 * 1024) < len(chunk):
                    print(f"HTTP OTA upload: {sent}/{image_size} bytes", flush=True)
        refresh_socket_timeout()
        connection.send(closing)
        refresh_socket_timeout()

        response = connection.getresponse()
        response_body = response.read().decode("utf-8", errors="replace").strip()
        if response.status != 200 or not response_body.startswith("OK"):
            raise RuntimeError(f"Robot rejected HTTP OTA ({response.status}): {response_body}")

        elapsed = time.monotonic() - started
        print(f"HTTP OTA accepted by robot in {elapsed:.1f}s")
        return response_body
    except (OSError, socket.error, TimeoutError) as exc:
        raise RuntimeError(f"HTTP OTA transport failed for {host}: {exc}") from exc
    finally:
        connection.close()


def preflight_robot(host: str) -> dict:
    """Reject stale/unready targets before starting an OTA transaction."""
    host = normalize_robot_host(host)
    try:
        health = request_json(f"http://{host}/api/v1/health", 3.0)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Robot preflight failed for {host}: {exc}") from exc
    if health.get("status") != "ok":
        raise RuntimeError(f"Robot preflight failed for {host}: invalid health response")
    if health.get("ready") is not True:
        raise RuntimeError(f"Robot preflight failed for {host}: robot is not ready")
    if health.get("network_ready") is not True:
        raise RuntimeError(f"Robot preflight failed for {host}: network is not ready")
    if health.get("http_ota") is not True:
        raise RuntimeError(f"Robot preflight failed for {host}: HTTP OTA is unavailable")
    return health


def _copy_program_header_safely(source: Path, destination: Path) -> bytes | None:
    """Install generated_program.h while preserving the previous image on failure."""
    previous = destination.read_bytes() if destination.is_file() else None
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return previous


def _restore_program_header(destination: Path, previous: bytes | None) -> None:
    if previous is None:
        try:
            destination.unlink()
        except FileNotFoundError:
            pass
    else:
        destination.write_bytes(previous)


def main() -> int:
    parser = argparse.ArgumentParser(description="Deploy a student RoboSim program or bootstrap a new robot")
    parser.add_argument("--input", help="Student RoboSim .py source; not required for bootstrap")
    parser.add_argument("--mode", choices=("build", "usb", "bootstrap", "ota"), default="build")
    parser.add_argument("--port", help="USB serial port for --mode usb/bootstrap")
    parser.add_argument("--robot", help="Robot hostname/IP for --mode ota, e.g. robot-A1B2C3.local")
    parser.add_argument("--ssid", help="Wi-Fi SSID used to build the robot firmware")
    parser.add_argument("--wifi-password", default=None, help="Wi-Fi password; prefer ROBOT_WIFI_PASSWORD")
    parser.add_argument("--ota-password", default=None, help="ArduinoOTA/HTTP OTA password; prefer ROBOT_OTA_PASSWORD")
    parser.add_argument("--bootstrap-config", help="RoboStudio-generated first-flash bootstrap JSON")
    parser.add_argument("--process-timeout", type=float, default=DEFAULT_PROCESS_TIMEOUT_SECONDS,
                        help="Maximum runtime for each external build/upload command (seconds)")
    parser.add_argument("--verify-timeout", type=float, default=30.0,
                        help="Maximum time to wait for the robot to become ready after OTA (seconds)")
    args = parser.parse_args()

    if args.process_timeout <= 0:
        parser.error("--process-timeout must be greater than zero")
    if args.verify_timeout <= 0:
        parser.error("--verify-timeout must be greater than zero")

    if args.mode == "bootstrap":
        if not args.bootstrap_config:
            parser.error("--mode bootstrap requires --bootstrap-config")
        return flash_bootstrap(Path(args.bootstrap_config), args.port)

    if not args.input:
        parser.error("--input is required unless --mode bootstrap is used")

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
        try:
            normalize_robot_host(args.robot)
        except ValueError as exc:
            parser.error(str(exc))

    project_name = source.stem
    build_dir = BUILD_ROOT / project_name
    build_dir.mkdir(parents=True, exist_ok=True)
    rewritten = build_dir / f"{project_name}.rewrite.py"
    header = build_dir / "program.h"
    report = build_dir / "compile_report.json"
    manifest_path = build_dir / "deployment_manifest.json"

    run([sys.executable, str(ROOT / "tools" / "rewrite.py"), "--input", str(source), "--output", str(rewritten)],
        timeout=args.process_timeout)
    run([sys.executable, str(ROOT / "tools" / "compile.py"), "--input", str(rewritten), "--output", str(header), "--report", str(report)],
        timeout=args.process_timeout)

    capabilities = infer_capabilities(header)
    platformio_environment = "esp32dev_ota" if args.mode == "ota" else "esp32dev"
    manifest = create_manifest(build_dir, "esp32", capabilities, source_path=source, platformio_environment=platformio_environment)
    manifest_dict = manifest.to_dict()
    write_manifest(manifest, manifest_path)
    validate_manifest(manifest_path, expected_target="esp32")

    platform_header = PLATFORM / "main" / "src" / "Application" / "generated_program.h"
    previous_header = None
    try:
        previous_header = _copy_program_header_safely(header, platform_header)
        print(f"Validated deployment manifest: {manifest_path}")
        print(f"Capabilities: {', '.join(capabilities)}")

        env = deployment_runtime_environment(os.environ.copy())
        if wifi_ssid:
            env["ROBOT_WIFI_SSID"] = wifi_ssid
            env["ROBOT_WIFI_PASSWORD"] = wifi_password
        if ota_password:
            env["ROBOT_OTA_PASSWORD"] = ota_password

        if args.mode == "build":
            run(platformio_command("run", "-e", "esp32dev"), cwd=PLATFORM, env=env,
                timeout=args.process_timeout)
        elif args.mode == "usb":
            command = platformio_command("run", "-e", "esp32dev", "-t", "upload")
            if args.port:
                command.extend(["--upload-port", args.port])
            run(command, cwd=PLATFORM, env=env, timeout=args.process_timeout)
        else:
            preflight_robot(args.robot)
            run(platformio_command("run", "-e", "esp32dev_ota"), cwd=PLATFORM, env=env,
                timeout=args.process_timeout)
            firmware = PLATFORM / ".pio" / "build" / "esp32dev_ota" / "firmware.bin"
            http_ota_upload(args.robot, ota_password, firmware)
            health = wait_for_robot(args.robot, timeout=args.verify_timeout)
            print(f"Robot READY: {health.get('hostname')} @ {health.get('ip')}")
    except Exception:
        _restore_program_header(platform_header, previous_header)
        raise

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
