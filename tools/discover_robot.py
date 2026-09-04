#!/usr/bin/env python3
"""Discover AnTechKids robots on the local LAN.

The utility uses the H27-A UDP discovery contract and prints machine-readable
JSON records. It intentionally has no dependency on PlatformIO or ESP32 tools.
"""

from __future__ import annotations

import argparse
import ipaddress
import json
import re
import socket
import time

DISCOVERY_PORT = 4210
REQUEST = b"ANTECHKIDS_ROBOT_DISCOVER_V1"
RESPONSE_PREFIX = b"ANTECHKIDS_ROBOT_INFO_V1\n"
PROTOCOL = "antechkids.robot.v1"
SCHEMA_VERSION = 1
DEVICE_ID_RE = re.compile(r"^robot-[0-9A-F]{12}$")
HOSTNAME_RE = re.compile(r"^robot-[0-9A-F]{6}\.local$")
REQUIRED_FIELDS = {
    "protocol",
    "schema_version",
    "device_id",
    "name",
    "hostname",
    "ip",
    "target",
    "firmware",
    "robot_ready",
    "network_ready",
    "ready",
    "ota",
    "capabilities",
}


def validate_robot_record(payload: object) -> bool:
    """Return True only for a complete, type-safe H27-A identity record."""
    if not isinstance(payload, dict) or not REQUIRED_FIELDS.issubset(payload):
        return False
    if payload["protocol"] != PROTOCOL or payload["schema_version"] != SCHEMA_VERSION:
        return False
    device_id = payload["device_id"]
    hostname = payload["hostname"]
    if not isinstance(device_id, str) or not DEVICE_ID_RE.fullmatch(device_id):
        return False
    if not isinstance(hostname, str) or not HOSTNAME_RE.fullmatch(hostname):
        return False
    if hostname != f"robot-{device_id[-6:]}.local":
        return False
    for field in ("name", "target", "firmware"):
        if not isinstance(payload[field], str) or not payload[field]:
            return False
    try:
        ipaddress.ip_address(payload["ip"])
    except ValueError:
        return False
    for field in ("robot_ready", "network_ready", "ready", "ota"):
        if not isinstance(payload[field], bool):
            return False
    if payload["ready"] != (payload["robot_ready"] and payload["network_ready"]):
        return False
    capabilities = payload["capabilities"]
    if not isinstance(capabilities, dict):
        return False
    if not all(isinstance(value, bool) for value in capabilities.values()):
        return False
    return True


def discover(timeout: float = 1.5) -> list[dict]:
    """Broadcast a discovery request and return unique validated robot records."""
    records: dict[str, dict] = {}
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(0.1)
        sock.sendto(REQUEST, ("255.255.255.255", DISCOVERY_PORT))
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                data, address = sock.recvfrom(4096)
            except socket.timeout:
                continue
            if not data.startswith(RESPONSE_PREFIX):
                continue
            try:
                payload = json.loads(data[len(RESPONSE_PREFIX) :].decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
            payload["ip"] = address[0]
            if validate_robot_record(payload):
                records[payload["device_id"]] = payload
    finally:
        sock.close()
    return list(records.values())


def main() -> int:
    parser = argparse.ArgumentParser(description="Discover AnTechKids robots on the local LAN")
    parser.add_argument("--timeout", type=float, default=1.5, help="Discovery window in seconds")
    args = parser.parse_args()

    robots = discover(max(0.1, args.timeout))
    print(json.dumps(robots, indent=2, sort_keys=True))
    return 0 if robots else 1


if __name__ == "__main__":
    raise SystemExit(main())
