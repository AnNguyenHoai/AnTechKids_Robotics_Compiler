"""RoboStudio-side robot discovery client.

Consumes the H27-A discovery/identity protocol and returns validated
RobotInfo records to the UI. The module has no Qt dependency so it is also
usable from tests and future non-GUI clients.
"""
from __future__ import annotations

import json
import socket
from dataclasses import dataclass, field
from typing import Any

DISCOVERY_PORT = 4210
DISCOVERY_REQUEST = b"ANTECHKIDS_ROBOT_DISCOVER_V1"
DISCOVERY_RESPONSE_PREFIX = "ANTECHKIDS_ROBOT_INFO_V1"
DISCOVERY_SCHEMA = 1
DISCOVERY_TIMEOUT_SECONDS = 1.5


class RobotDiscoveryError(RuntimeError):
    """Raised when discovery cannot be performed."""


@dataclass(frozen=True)
class RobotInfo:
    device_id: str
    name: str
    hostname: str
    ip: str
    target: str
    firmware: str
    robot_ready: bool
    network_ready: bool
    ready: bool
    ota: bool
    capabilities: dict[str, bool] = field(default_factory=dict)
    schema_version: int = DISCOVERY_SCHEMA
    protocol: str = "antechkids.robot.v1"

    @property
    def display_label(self) -> str:
        return self.name or self.hostname or self.device_id


def _required_string(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"missing/invalid {key}")
    return value.strip()


def serialize_robot_info(info: RobotInfo) -> dict[str, Any]:
    """Serialize one validated identity snapshot using the canonical H27 schema."""
    return {
        "protocol": info.protocol,
        "schema_version": info.schema_version,
        "device_id": info.device_id,
        "name": info.name,
        "hostname": info.hostname,
        "ip": info.ip,
        "target": info.target,
        "firmware": info.firmware,
        "robot_ready": info.robot_ready,
        "network_ready": info.network_ready,
        "ready": info.ready,
        "ota": info.ota,
        "capabilities": dict(info.capabilities),
    }


def validate_robot_info(data: Any, source_ip: str | None = None) -> RobotInfo:
    """Validate the canonical H27-A identity payload."""
    if not isinstance(data, dict):
        raise ValueError("identity payload must be an object")
    if data.get("protocol") != "antechkids.robot.v1":
        raise ValueError("unsupported robot protocol")
    if data.get("schema_version") != DISCOVERY_SCHEMA:
        raise ValueError("unsupported robot identity schema")

    device_id = _required_string(data, "device_id")
    name = _required_string(data, "name")
    hostname = _required_string(data, "hostname")
    target = _required_string(data, "target")
    firmware = _required_string(data, "firmware")

    ip = data.get("ip")
    if not isinstance(ip, str) or not ip.strip():
        ip = source_ip or ""
    if not ip:
        raise ValueError("missing/invalid ip")

    for key in ("robot_ready", "network_ready", "ready", "ota"):
        if not isinstance(data.get(key), bool):
            raise ValueError(f"missing/invalid {key}")

    capabilities = data.get("capabilities")
    if not isinstance(capabilities, dict) or any(
        not isinstance(key, str) or not isinstance(value, bool)
        for key, value in capabilities.items()
    ):
        raise ValueError("missing/invalid capabilities")

    return RobotInfo(
        device_id=device_id,
        name=name,
        hostname=hostname,
        ip=ip.strip(),
        target=target,
        firmware=firmware,
        robot_ready=data["robot_ready"],
        network_ready=data["network_ready"],
        ready=data["ready"],
        ota=data["ota"],
        capabilities=dict(capabilities),
        schema_version=data["schema_version"],
        protocol=data["protocol"],
    )


class RobotDiscoveryClient:
    """Discover robots on the local LAN using the H27-A UDP protocol."""

    def __init__(self, port: int = DISCOVERY_PORT, timeout: float = DISCOVERY_TIMEOUT_SECONDS):
        self.port = port
        self.timeout = timeout

    def discover(self) -> list[RobotInfo]:
        """Broadcast a discovery request and collect unique valid robots."""
        robots: dict[str, RobotInfo] = {}
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.settimeout(self.timeout)
            sock.sendto(DISCOVERY_REQUEST, ("255.255.255.255", self.port))
            while True:
                try:
                    packet, address = sock.recvfrom(4096)
                except socket.timeout:
                    break
                try:
                    text = packet.decode("utf-8").strip()
                    prefix, payload = text.split("\n", 1)
                    if prefix != DISCOVERY_RESPONSE_PREFIX:
                        continue
                    info = validate_robot_info(json.loads(payload), address[0])
                except (UnicodeDecodeError, ValueError, json.JSONDecodeError):
                    continue
                robots[info.device_id] = info
        except OSError as exc:
            raise RobotDiscoveryError(f"Robot discovery failed: {exc}") from exc
        finally:
            sock.close()
        return sorted(robots.values(), key=lambda robot: robot.display_label.lower())

    def get_info(self, host: str, timeout: float = 2.0) -> RobotInfo:
        """Fetch and validate identity from a specific robot."""
        import urllib.request
        url = f"http://{host}/api/v1/info"
        try:
            with urllib.request.urlopen(url, timeout=timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            raise RobotDiscoveryError(f"Unable to read robot info from {host}: {exc}") from exc
        return validate_robot_info(data, host)
