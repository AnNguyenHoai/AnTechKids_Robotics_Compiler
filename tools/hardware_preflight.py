"""B2.4 hardware/flash portability preflight.

USB flashing must never guess a developer-machine COM port or rely on a host
PlatformIO installation. Port discovery is executed through the canonical
application-owned PlatformIO command and the B2.2/B2.3 sealed deployment
boundary. The Windows USB/UART driver remains an OS prerequisite; successful
enumeration is the objective proof that the selected bridge is visible to the
application.
"""
from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

from tools import build_isolation
from tools.deployment_runtime import (
    DeploymentRuntimeError,
    deployment_runtime_environment,
    platformio_command,
    run_process,
)

PREFLIGHT_PROJECT = "hardware-preflight"
SCHEMA = "antechkids.robostudio.hardware-flash-preflight"
SCHEMA_VERSION = 1


class HardwarePreflightError(RuntimeError):
    """Raised when USB hardware is not ready for a deterministic flash."""


@dataclass(frozen=True)
class SerialPortInfo:
    port: str
    description: str = ""
    hwid: str = ""
    vid: str = ""
    pid: str = ""
    serial_number: str = ""
    manufacturer: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "port": self.port,
            "description": self.description,
            "hwid": self.hwid,
            "vid": self.vid,
            "pid": self.pid,
            "serial_number": self.serial_number,
            "manufacturer": self.manufacturer,
        }


@dataclass(frozen=True)
class HardwarePreflightReport:
    requested_port: str
    selected_port: SerialPortInfo
    detected_ports: tuple[SerialPortInfo, ...]
    discovery_command: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": SCHEMA,
            "schema_version": SCHEMA_VERSION,
            "status": "PASS",
            "requested_port": self.requested_port,
            "selected_port": self.selected_port.to_dict(),
            "detected_ports": [item.to_dict() for item in self.detected_ports],
            "discovery": {
                "provider": "packaged-platformio",
                "command_tail": ["device", "list", "--json-output"],
                "host_path_lookup": False,
            },
            "driver_visibility_proven": True,
        }


def _string(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, int):
        return str(value)
    return str(value).strip()


def parse_device_list(output: str) -> tuple[SerialPortInfo, ...]:
    """Parse ``platformio device list --json-output`` deterministically."""
    try:
        data = json.loads(output)
    except json.JSONDecodeError as exc:
        raise HardwarePreflightError(
            "Packaged PlatformIO returned invalid serial-device JSON."
        ) from exc
    if not isinstance(data, list):
        raise HardwarePreflightError(
            "Packaged PlatformIO serial-device response must be a JSON array."
        )

    ports: list[SerialPortInfo] = []
    seen: set[str] = set()
    for raw in data:
        if not isinstance(raw, dict):
            continue
        port = _string(raw.get("port"))
        if not port:
            continue
        key = port.casefold()
        if key in seen:
            continue
        seen.add(key)
        ports.append(
            SerialPortInfo(
                port=port,
                description=_string(raw.get("description")),
                hwid=_string(raw.get("hwid")),
                vid=_string(raw.get("vid")),
                pid=_string(raw.get("pid")),
                serial_number=_string(raw.get("serial_number")),
                manufacturer=_string(raw.get("manufacturer")),
            )
        )
    return tuple(sorted(ports, key=lambda item: item.port.casefold()))


def _display_ports(ports: Sequence[SerialPortInfo]) -> str:
    if not ports:
        return "none"
    return ", ".join(
        f"{item.port} ({item.description})" if item.description else item.port
        for item in ports
    )


def select_serial_port(
    requested_port: str | None,
    ports: Sequence[SerialPortInfo],
) -> SerialPortInfo:
    """Require an explicit visible serial port; never guess the first device."""
    requested = (requested_port or "").strip()
    if not requested:
        raise HardwarePreflightError(
            "USB flash requires an explicit COM/serial port. "
            f"Detected ports: {_display_ports(ports)}."
        )
    if not ports:
        raise HardwarePreflightError(
            f"Serial port {requested!r} is not visible. No serial/COM ports were detected. "
            "Reconnect the robot and install the USB/UART bridge driver required by the board."
        )
    for item in ports:
        # B2.4 production support is Windows; case-insensitive matching also
        # keeps synthetic qualification fixtures deterministic on non-Windows CI.
        if item.port.casefold() == requested.casefold():
            return item
    raise HardwarePreflightError(
        f"Serial port {requested!r} is not visible. Detected ports: {_display_ports(ports)}. "
        "Select a detected robot port; RoboStudio will not fall back to a default COM port."
    )


def discover_serial_ports(
    *,
    base_env: Mapping[str, str] | None = None,
    timeout: float = 30.0,
) -> tuple[tuple[SerialPortInfo, ...], tuple[str, ...]]:
    """Enumerate ports through artifact-owned PlatformIO and external state."""
    if timeout <= 0:
        raise ValueError("Hardware preflight timeout must be greater than zero.")
    inherited = dict(os.environ if base_env is None else base_env)
    try:
        workspace = build_isolation.prepare_build_workspace(
            PREFLIGHT_PROJECT, base_env=inherited
        )
        env = deployment_runtime_environment(inherited, project_name=PREFLIGHT_PROJECT)
        command = tuple(platformio_command("device", "list", "--json-output"))
        result = run_process(command, cwd=workspace, env=env, timeout=timeout)
    except (DeploymentRuntimeError, OSError) as exc:
        raise HardwarePreflightError(
            f"Unable to enumerate USB serial devices with packaged PlatformIO: {exc}"
        ) from exc
    if result.returncode != 0:
        detail = result.output.strip()
        suffix = f"\n{detail}" if detail else ""
        raise HardwarePreflightError(
            "Packaged PlatformIO could not enumerate USB serial devices." + suffix
        )
    return parse_device_list(result.output), command


def require_serial_port(
    requested_port: str | None,
    *,
    base_env: Mapping[str, str] | None = None,
    timeout: float = 30.0,
) -> HardwarePreflightReport:
    """Prove that an explicitly selected port is currently visible."""
    ports, command = discover_serial_ports(base_env=base_env, timeout=timeout)
    selected = select_serial_port(requested_port, ports)
    return HardwarePreflightReport(
        requested_port=(requested_port or "").strip(),
        selected_port=selected,
        detected_ports=ports,
        discovery_command=command,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate a USB/COM port through RoboStudio's packaged PlatformIO runtime"
    )
    parser.add_argument("--port", required=True)
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    try:
        report = require_serial_port(args.port, timeout=args.timeout)
    except HardwarePreflightError as exc:
        if args.as_json:
            print(json.dumps({"schema": SCHEMA, "schema_version": SCHEMA_VERSION, "status": "FAIL", "error": str(exc)}, indent=2))
        else:
            print(f"B2.4 hardware preflight: FAIL\n{exc}")
        return 1
    if args.as_json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print(f"B2.4 hardware preflight: PASS ({report.selected_port.port})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
