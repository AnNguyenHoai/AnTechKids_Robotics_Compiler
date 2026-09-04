#!/usr/bin/env python3
"""Discover AnTechKids robots on the local LAN.

The utility uses the H27-A UDP discovery contract and prints machine-readable
JSON records. It intentionally has no dependency on PlatformIO or ESP32 tools.
"""

from __future__ import annotations

import argparse
import json
import socket
import time

DISCOVERY_PORT = 4210
REQUEST = b"ANTECHKIDS_ROBOT_DISCOVER_V1"
RESPONSE_PREFIX = b"ANTECHKIDS_ROBOT_INFO_V1\n"


def discover(timeout: float = 1.5) -> list[dict]:
    """Broadcast a discovery request and return unique robot records."""
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
            payload.setdefault("ip", address[0])
            device_id = payload.get("device_id")
            if device_id:
                records[device_id] = payload
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
